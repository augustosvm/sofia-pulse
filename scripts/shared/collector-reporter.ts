/**
 * Collector Reporter - Standardized output for all collectors
 *
 * Garante que todos os coletores reportam estatísticas de forma consistente
 * para que o sistema de notificações WhatsApp capture os números corretamente.
 */

export interface CollectorStats {
  collectorName: string;
  collected: number;
  errors?: number;
  updated?: number;
  skipped?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

export class CollectorReporter {
  private startTime: number;
  private collectorName: string;

  constructor(collectorName: string) {
    this.collectorName = collectorName;
    this.startTime = Date.now();
  }

  /**
   * Report final statistics (REQUIRED)
   * This is the standard format that notifications expect
   */
  reportSuccess(stats: Omit<CollectorStats, 'collectorName'>): void {
    const duration = stats.duration || (Date.now() - this.startTime) / 1000;

    console.log('\n' + '='.repeat(60));
    console.log(`✅ ${this.collectorName} - Collection Complete`);
    console.log('='.repeat(60));

    // PRIMARY METRIC - This line is REQUIRED for WhatsApp notifications
    console.log(`📊 Collected: ${stats.collected} records`);

    if (stats.updated !== undefined) {
      console.log(`🔄 Updated: ${stats.updated} records`);
    }

    if (stats.skipped !== undefined) {
      console.log(`⏭️  Skipped: ${stats.skipped} (duplicates)`);
    }

    if (stats.errors && stats.errors > 0) {
      console.log(`⚠️  Errors: ${stats.errors}`);
    }

    console.log(`⏱️  Duration: ${duration.toFixed(2)}s`);

    if (stats.metadata) {
      console.log('\n📈 Additional Stats:');
      Object.entries(stats.metadata).forEach(([key, value]) => {
        console.log(`   • ${key}: ${value}`);
      });
    }

    console.log('='.repeat(60));
  }

  /**
   * Report failure (for critical errors)
   */
  reportFailure(error: Error | string): void {
    const errorMessage = error instanceof Error ? error.message : error;

    console.log('\n' + '='.repeat(60));
    console.log(`❌ ${this.collectorName} - Collection Failed`);
    console.log('='.repeat(60));
    console.log(`Error: ${errorMessage}`);
    console.log('='.repeat(60));
  }

  /**
   * Report progress (optional, for long-running collectors)
   */
  reportProgress(message: string, current?: number, total?: number): void {
    if (current !== undefined && total !== undefined) {
      const percent = ((current / total) * 100).toFixed(1);
      console.log(`🔄 ${message} [${current}/${total}] (${percent}%)`);
    } else {
      console.log(`🔄 ${message}`);
    }
  }

  /**
   * Get elapsed time
   */
  getElapsedTime(): number {
    return (Date.now() - this.startTime) / 1000;
  }
}

/**
 * Quick helper for simple collectors
 */
export function reportCollectorSuccess(collectorName: string, collected: number, errors: number = 0): void {
  const reporter = new CollectorReporter(collectorName);
  reporter.reportSuccess({ collected, errors });
}

/**
 * Quick helper for failed collectors
 */
export function reportCollectorFailure(collectorName: string, error: Error | string): void {
  const reporter = new CollectorReporter(collectorName);
  reporter.reportFailure(error);
}
