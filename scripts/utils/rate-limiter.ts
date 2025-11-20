/**
 * Rate Limiter Utility
 *
 * Handles API rate limiting with:
 * - Exponential backoff
 * - Configurable delays
 * - Rate limit detection
 * - Retry logic
 */

import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

export interface RateLimiterConfig {
  /** Delay between requests in milliseconds (default: 1000) */
  delayBetweenRequests?: number;

  /** Maximum number of retries (default: 4) */
  maxRetries?: number;

  /** Initial backoff delay in milliseconds (default: 2000) */
  initialBackoffMs?: number;

  /** Maximum backoff delay in milliseconds (default: 32000) */
  maxBackoffMs?: number;

  /** Whether to check rate limit headers (default: true) */
  checkRateLimitHeaders?: boolean;

  /** Custom function to determine if error is rate limit (default: checks 403/429) */
  isRateLimitError?: (error: any) => boolean;
}

export class RateLimiter {
  private config: Required<RateLimiterConfig>;
  private lastRequestTime: number = 0;
  private rateLimitRemaining: number | null = null;
  private rateLimitReset: number | null = null;

  constructor(config: RateLimiterConfig = {}) {
    this.config = {
      delayBetweenRequests: config.delayBetweenRequests ?? 1000,
      maxRetries: config.maxRetries ?? 4,
      initialBackoffMs: config.initialBackoffMs ?? 2000,
      maxBackoffMs: config.maxBackoffMs ?? 32000,
      checkRateLimitHeaders: config.checkRateLimitHeaders ?? true,
      isRateLimitError: config.isRateLimitError ?? this.defaultIsRateLimitError,
    };
  }

  /**
   * Default check for rate limit errors (403 or 429 status codes)
   */
  private defaultIsRateLimitError(error: any): boolean {
    return error?.response?.status === 403 || error?.response?.status === 429;
  }

  /**
   * Wait for the configured delay between requests
   */
  private async waitForDelay(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;

    if (timeSinceLastRequest < this.config.delayBetweenRequests) {
      const waitTime = this.config.delayBetweenRequests - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.lastRequestTime = Date.now();
  }

  /**
   * Calculate exponential backoff delay
   */
  private calculateBackoff(retryCount: number): number {
    const backoff = this.config.initialBackoffMs * Math.pow(2, retryCount);
    return Math.min(backoff, this.config.maxBackoffMs);
  }

  /**
   * Extract and update rate limit info from response headers
   */
  private updateRateLimitInfo(response: AxiosResponse): void {
    if (!this.config.checkRateLimitHeaders) return;

    // GitHub-style headers
    const remaining = response.headers['x-ratelimit-remaining'];
    const reset = response.headers['x-ratelimit-reset'];

    if (remaining !== undefined) {
      this.rateLimitRemaining = parseInt(remaining, 10);
    }

    if (reset !== undefined) {
      this.rateLimitReset = parseInt(reset, 10) * 1000; // Convert to ms
    }

    // Log warning if rate limit is low
    if (this.rateLimitRemaining !== null && this.rateLimitRemaining < 10) {
      const resetDate = this.rateLimitReset ? new Date(this.rateLimitReset).toISOString() : 'unknown';
      console.log(`⚠️  Rate limit low: ${this.rateLimitRemaining} remaining (resets at ${resetDate})`);
    }
  }

  /**
   * Wait until rate limit resets if we're rate limited
   */
  private async waitForRateLimitReset(): Promise<void> {
    if (this.rateLimitReset) {
      const now = Date.now();
      const waitTime = Math.max(0, this.rateLimitReset - now + 1000); // +1s buffer

      if (waitTime > 0) {
        console.log(`⏳ Rate limit exceeded. Waiting ${Math.ceil(waitTime / 1000)}s until reset...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  /**
   * Make an HTTP request with rate limiting and retry logic
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    let lastError: any;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        // Wait for delay between requests
        await this.waitForDelay();

        // Check if we should wait for rate limit reset
        if (this.rateLimitRemaining !== null && this.rateLimitRemaining === 0) {
          await this.waitForRateLimitReset();
        }

        // Make the request
        const response = await axios.request<T>(config);

        // Update rate limit info from headers
        this.updateRateLimitInfo(response);

        return response;

      } catch (error: any) {
        lastError = error;

        // Check if it's a rate limit error
        if (this.config.isRateLimitError(error)) {
          // Update rate limit info if available
          if (error.response) {
            this.updateRateLimitInfo(error.response);
          }

          // If we have retries left, wait and try again
          if (attempt < this.config.maxRetries) {
            const backoffDelay = this.calculateBackoff(attempt);
            console.log(`⏳ Rate limit hit (attempt ${attempt + 1}/${this.config.maxRetries + 1}). Waiting ${backoffDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, backoffDelay));
            continue;
          }
        }

        // If it's not a rate limit error, or we're out of retries, throw
        throw error;
      }
    }

    // If we get here, we ran out of retries
    throw lastError;
  }

  /**
   * Make a GET request with rate limiting
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  /**
   * Make a POST request with rate limiting
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  /**
   * Get current rate limit status
   */
  getRateLimitStatus(): { remaining: number | null; reset: Date | null } {
    return {
      remaining: this.rateLimitRemaining,
      reset: this.rateLimitReset ? new Date(this.rateLimitReset) : null,
    };
  }
}

/**
 * Pre-configured rate limiters for common APIs
 */
export const rateLimiters = {
  /** GitHub API (5000/hour with token, 60/hour without) */
  github: new RateLimiter({
    delayBetweenRequests: 1000,
    maxRetries: 4,
    initialBackoffMs: 2000,
  }),

  /** Reddit API (60/minute) */
  reddit: new RateLimiter({
    delayBetweenRequests: 1100, // ~60/min with buffer
    maxRetries: 4,
    initialBackoffMs: 5000,
  }),

  /** NPM API (no official limit, but be conservative) */
  npm: new RateLimiter({
    delayBetweenRequests: 500,
    maxRetries: 3,
    initialBackoffMs: 2000,
  }),

  /** Generic API (conservative defaults) */
  generic: new RateLimiter({
    delayBetweenRequests: 2000,
    maxRetries: 4,
    initialBackoffMs: 3000,
  }),
};

/**
 * Helper function to create a custom rate limiter
 */
export function createRateLimiter(config: RateLimiterConfig): RateLimiter {
  return new RateLimiter(config);
}
