"""
Collector Reporter - Standardized output for all collectors

Garante que todos os coletores reportam estatísticas de forma consistente
para que o sistema de notificações WhatsApp capture os números corretamente.
"""

import time
from typing import Dict, Any, Optional


class CollectorReporter:
    """Standardized reporting for collectors"""

    def __init__(self, collector_name: str):
        self.collector_name = collector_name
        self.start_time = time.time()

    def report_success(
        self,
        collected: int,
        errors: int = 0,
        updated: Optional[int] = None,
        skipped: Optional[int] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Report final statistics (REQUIRED)
        This is the standard format that notifications expect
        """
        actual_duration = duration or (time.time() - self.start_time)

        print('\n' + '=' * 60)
        print(f'✅ {self.collector_name} - Collection Complete')
        print('=' * 60)

        # PRIMARY METRIC - This line is REQUIRED for WhatsApp notifications
        print(f'📊 Collected: {collected} records')

        if updated is not None:
            print(f'🔄 Updated: {updated} records')

        if skipped is not None:
            print(f'⏭️  Skipped: {skipped} (duplicates)')

        if errors > 0:
            print(f'⚠️  Errors: {errors}')

        print(f'⏱️  Duration: {actual_duration:.2f}s')

        if metadata:
            print('\n📈 Additional Stats:')
            for key, value in metadata.items():
                print(f'   • {key}: {value}')

        print('=' * 60)

    def report_failure(self, error: Exception | str) -> None:
        """Report failure (for critical errors)"""
        error_message = str(error)

        print('\n' + '=' * 60)
        print(f'❌ {self.collector_name} - Collection Failed')
        print('=' * 60)
        print(f'Error: {error_message}')
        print('=' * 60)

    def report_progress(
        self,
        message: str,
        current: Optional[int] = None,
        total: Optional[int] = None
    ) -> None:
        """Report progress (optional, for long-running collectors)"""
        if current is not None and total is not None:
            percent = (current / total) * 100
            print(f'🔄 {message} [{current}/{total}] ({percent:.1f}%)')
        else:
            print(f'🔄 {message}')

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time


def report_collector_success(
    collector_name: str,
    collected: int,
    errors: int = 0
) -> None:
    """Quick helper for simple collectors"""
    reporter = CollectorReporter(collector_name)
    reporter.report_success(collected=collected, errors=errors)


def report_collector_failure(
    collector_name: str,
    error: Exception | str
) -> None:
    """Quick helper for failed collectors"""
    reporter = CollectorReporter(collector_name)
    reporter.report_failure(error)
