#!/usr/bin/env python3
"""
Sofia Pulse - Retry Logic with Exponential Backoff
Protection against API failures and rate limits
"""

import random
import time
from functools import wraps

import requests


def retry_with_backoff(max_retries=5, base_delay=2, max_delay=32, jitter=True):
    """
    Decorator for retry with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter to avoid thundering herd

    Usage:
        @retry_with_backoff(max_retries=5)
        def fetch_data():
            return requests.get(url)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (
                    requests.exceptions.RequestException,
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                ) as e:

                    if attempt == max_retries - 1:
                        raise  # Last attempt failed, re-raise

                    # Calculate backoff delay
                    delay = min(base_delay * (2**attempt), max_delay)

                    # Add jitter (random 0-100% of delay)
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)

                    print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"   Retrying in {delay:.1f}s...")

                    time.sleep(delay)

            return None  # Should never reach here

        return wrapper

    return decorator


def safe_request(url, headers=None, timeout=15, max_retries=5):
    """
    Make HTTP request with retry and backoff

    Args:
        url: URL to fetch
        headers: Optional headers dict
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Response object or None if all retries failed
    """
    if headers is None:
        headers = {"User-Agent": "SofiaPulse/1.0 (Tech Intelligence; +https://github.com/augustosvm/sofia-pulse)"}

    for attempt in range(max_retries):
        try:
            # Random delay to avoid rate limits
            time.sleep(random.uniform(0.5, 2.0))

            response = requests.get(url, headers=headers, timeout=timeout)

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"⚠️  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue

            # Check for success
            if response.status_code == 200:
                return response

            # Other errors
            if response.status_code >= 400:
                print(f"⚠️  HTTP {response.status_code}: {url}")

                # Don't retry on client errors (except 429)
                if 400 <= response.status_code < 500:
                    return None

        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout on attempt {attempt + 1}/{max_retries}")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Connection error on attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")

        # Calculate backoff
        if attempt < max_retries - 1:
            delay = min(2**attempt, 32)
            delay = delay * (0.5 + random.random() * 0.5)  # Jitter
            print(f"   Retrying in {delay:.1f}s...")
            time.sleep(delay)

    print(f"❌ All {max_retries} attempts failed for: {url}")
    return None
