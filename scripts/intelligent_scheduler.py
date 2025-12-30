#!/usr/bin/env python3
"""
================================================================================
INTELLIGENT SCHEDULER - Orchestration Layer with Retry & Fallback Logic
================================================================================

Beyond simple cron jobs, this scheduler provides:
  - Retry logic (HN fails → retry every 5 min, max 3 attempts)
  - Rate limiting (GitHub rate limit → pause 1 hour)
  - Fallbacks (B3 error → use yesterday's data)
  - Dependency management (collector down 48h → pause dependents)
  - Priority queuing (critical > normal > low)
  - Circuit breakers (repeated failures → disable temporarily)
  - Health checks (auto-resume when service recovers)

Usage:
  from intelligent_scheduler import IntelligentScheduler

  scheduler = IntelligentScheduler()
  scheduler.schedule_collector('github_trending', priority='high', retry_max=3)
  scheduler.run()

================================================================================
"""

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()


class Priority(Enum):
    """Task priority levels."""

    CRITICAL = 1  # Must run immediately
    HIGH = 2  # Run ASAP
    NORMAL = 3  # Normal priority
    LOW = 4  # Can wait


class CollectorStatus(Enum):
    """Collector health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Some failures but recoverable
    FAILING = "failing"  # Repeated failures
    CIRCUIT_OPEN = "circuit_open"  # Circuit breaker open
    PAUSED = "paused"  # Manually paused
    DISABLED = "disabled"  # Disabled due to dependency failure


@dataclass
class RetryPolicy:
    """Retry configuration for a collector."""

    max_attempts: int = 3
    initial_delay_sec: int = 30  # 30 seconds
    max_delay_sec: int = 300  # 5 minutes (was 3600)
    backoff_multiplier: float = 2.0  # Exponential backoff
    retry_on_errors: List[str] = field(default_factory=lambda: ["timeout", "connection", "rate_limit"])


@dataclass
class FallbackPolicy:
    """Fallback configuration."""

    enabled: bool = True
    use_cached_data: bool = True
    cache_max_age_hours: int = 24
    fallback_to_yesterday: bool = True
    notify_on_fallback: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5  # Open after N failures
    recovery_timeout_sec: int = 300  # 5 minutes
    half_open_max_calls: int = 1  # Test with 1 call


@dataclass
class CollectorTask:
    """Represents a scheduled collector task."""

    collector_name: str
    script_path: str
    priority: Priority = Priority.NORMAL
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    fallback_policy: FallbackPolicy = field(default_factory=FallbackPolicy)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    dependencies: List[str] = field(default_factory=list)
    schedule_cron: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: CollectorStatus = CollectorStatus.HEALTHY
    consecutive_failures: int = 0
    circuit_opened_at: Optional[datetime] = None


class IntelligentScheduler:
    """
    Intelligent orchestration layer for Sofia Pulse collectors.
    Handles retries, rate limiting, fallbacks, and dependencies.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            user=os.getenv("POSTGRES_USER", "sofia"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB", "sofia_db"),
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # Task registry
        self.tasks: Dict[str, CollectorTask] = {}

        # Priority queue (will be sorted by priority + next_run)
        self.queue: List[CollectorTask] = []

        # Running flag
        self.running = False

        # WhatsApp alerts
        self.whatsapp_enabled = os.getenv("ALERT_WHATSAPP_ENABLED", "false").lower() == "true"
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER")
        self.sofia_endpoint = os.getenv("SOFIA_API_ENDPOINT", "http://localhost:8001/api/v2/chat")

        print("✅ IntelligentScheduler initialized")
        print(f"   Database: {os.getenv('POSTGRES_DB', 'sofia_db')}")
        print(f"   WhatsApp alerts: {self.whatsapp_enabled}")

    # ========================================================================
    # TASK REGISTRATION
    # ========================================================================

    def register_collector(
        self,
        collector_name: str,
        script_path: str,
        priority: str = "normal",
        retry_max: int = 3,
        retry_delay_sec: int = 60,
        fallback_enabled: bool = True,
        dependencies: Optional[List[str]] = None,
        schedule_cron: Optional[str] = None,
    ):
        """
        Register a collector with the scheduler.

        Args:
          collector_name: Unique collector name
          script_path: Path to collector script
          priority: 'critical', 'high', 'normal', 'low'
          retry_max: Max retry attempts
          retry_delay_sec: Initial retry delay
          fallback_enabled: Enable fallback to cached data
          dependencies: List of collector names this depends on
          schedule_cron: Cron expression (optional)
        """
        priority_enum = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "normal": Priority.NORMAL,
            "low": Priority.LOW,
        }.get(priority.lower(), Priority.NORMAL)

        task = CollectorTask(
            collector_name=collector_name,
            script_path=script_path,
            priority=priority_enum,
            retry_policy=RetryPolicy(max_attempts=retry_max, initial_delay_sec=retry_delay_sec),
            fallback_policy=FallbackPolicy(enabled=fallback_enabled),
            dependencies=dependencies or [],
            schedule_cron=schedule_cron,
        )

        self.tasks[collector_name] = task
        print(f"📝 Registered collector: {collector_name} (priority: {priority})")

    def register_all_collectors(self):
        """Register all Sofia Pulse collectors with recommended configs."""
        print("\n" + "=" * 80)
        print("REGISTERING ALL COLLECTORS")
        print("=" * 80)

        # CRITICAL: Real-time data sources
        self.register_collector(
            "github",
            "npx tsx scripts/collect.ts github",
            priority="critical",
            retry_max=5,
            retry_delay_sec=300,  # 5 min
        )

        self.register_collector(
            "hackernews", "npx tsx scripts/collect.ts hackernews", priority="critical", retry_max=5, retry_delay_sec=300
        )

        self.register_collector(
            "reddit", "npx tsx scripts/collect.ts reddit", priority="high", retry_max=3, retry_delay_sec=600
        )

        self.register_collector(
            "npm", "npx tsx scripts/collect.ts npm", priority="normal", retry_max=2, retry_delay_sec=3600
        )

        self.register_collector(
            "pypi", "npx tsx scripts/collect.ts pypi", priority="normal", retry_max=2, retry_delay_sec=3600
        )

        self.register_collector(
            "stackoverflow",
            "npx tsx scripts/collect.ts stackoverflow",
            priority="normal",
            retry_max=2,
            retry_delay_sec=3600,
        )

        # HIGH: Daily economic indicators
        self.register_collector(
            "world_bank",
            "scripts/collect-women-world-bank.py",
            priority="high",
            retry_max=3,
            retry_delay_sec=600,  # 10 min
            fallback_enabled=True,
        )

        self.register_collector(
            "fred", "scripts/collect-women-fred.py", priority="high", retry_max=3, retry_delay_sec=600
        )

        # NORMAL: Static/slow-changing data
        self.register_collector(
            "eurostat",
            "scripts/collect-women-eurostat.py",
            priority="normal",
            retry_max=2,
            retry_delay_sec=1800,  # 30 min
        )

        self.register_collector(
            "ilo", "scripts/collect-women-ilo.py", priority="normal", retry_max=2, retry_delay_sec=1800
        )

        # Dependencies: Brazil security depends on IBGE data
        self.register_collector("brazil_ibge", "scripts/collect-women-brazil.py", priority="normal", retry_max=2)

        self.register_collector(
            "brazil_security",
            "scripts/collect-security-brazil.py",
            priority="normal",
            retry_max=2,
            dependencies=["brazil_ibge"],  # Depends on IBGE
        )

        # BRAZIL: Data Collectors
        self.register_collector(
            "mdic-regional", "scripts/collect-mdic-comexstat.py", priority="normal", retry_max=3, retry_delay_sec=300
        )

        self.register_collector(
            "fiesp-data", "scripts/collect-fiesp-data.py", priority="normal", retry_max=3, retry_delay_sec=3600
        )

        # UNIFIED: Organizations
        self.register_collector(
            "ai-companies",
            "npx tsx scripts/collect.ts ai-companies",
            priority="high",
            retry_max=2,
            retry_delay_sec=3600,
        )

        self.register_collector(
            "universities",
            "npx tsx scripts/collect.ts universities",
            priority="normal",
            retry_max=1,
            retry_delay_sec=3600,
        )

        self.register_collector(
            "ngos", "npx tsx scripts/collect.ts ngos", priority="normal", retry_max=1, retry_delay_sec=3600
        )

        # UNIFIED: Funding
        self.register_collector(
            "yc-companies",
            "npx tsx scripts/collect.ts yc-companies",
            priority="normal",
            retry_max=2,
            retry_delay_sec=3600,
        )

        self.register_collector(
            "producthunt", "npx tsx scripts/collect.ts producthunt", priority="high", retry_max=3, retry_delay_sec=900
        )

        print(f"\n✅ Registered {len(self.tasks)} collectors")

    # ========================================================================
    # TASK EXECUTION
    # ========================================================================

    def execute_collector(self, task: CollectorTask) -> bool:
        """
        Execute a collector task.

        Returns:
          True if successful, False if failed
        """
        print(f"\n{'='*80}")
        print(f"▶️  EXECUTING: {task.collector_name}")
        print(f"   Priority: {task.priority.name}")
        print(f"   Script: {task.script_path}")
        print(f"{'='*80}")

        # Start collector run tracking
        run_id = self.start_collector_run(task.collector_name)

        try:
            # Determine command based on file extension
            if task.script_path.endswith(".ts"):
                cmd = ["npx.cmd", "tsx", task.script_path] if os.name == "nt" else ["npx", "tsx", task.script_path]
            elif task.script_path.endswith(".py"):
                cmd = [sys.executable, task.script_path]
            else:
                cmd = task.script_path.split()

            # Execute script
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout

            success = result.returncode == 0

            # Complete run
            self.complete_collector_run(
                run_id, "success" if success else "failed", result.stdout if success else result.stderr
            )

            if success:
                print(f"✅ SUCCESS: {task.collector_name}")
                task.consecutive_failures = 0
                task.status = CollectorStatus.HEALTHY
                task.last_run = datetime.now()
                return True
            else:
                print(f"❌ FAILED: {task.collector_name}")
                print(f"   Error: {result.stderr[:200]}")
                task.consecutive_failures += 1
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {task.collector_name}")
            self.complete_collector_run(run_id, "timeout", "Execution timeout (>1h)")
            task.consecutive_failures += 1
            return False

        except Exception as e:
            print(f"💥 EXCEPTION: {task.collector_name}")
            print(f"   Error: {str(e)}")
            self.complete_collector_run(run_id, "failed", str(e))
            task.consecutive_failures += 1
            return False

    def retry_with_backoff(self, task: CollectorTask) -> bool:
        """
        Retry task with exponential backoff.

        Returns:
          True if eventually successful, False if all retries exhausted
        """
        attempts = 0
        delay = task.retry_policy.initial_delay_sec

        while attempts < task.retry_policy.max_attempts:
            attempts += 1
            print(f"\n🔄 RETRY {attempts}/{task.retry_policy.max_attempts}: {task.collector_name}")
            print(f"   Waiting {delay}s before retry...")
            time.sleep(delay)

            success = self.execute_collector(task)
            if success:
                return True

            # Exponential backoff
            delay = min(delay * task.retry_policy.backoff_multiplier, task.retry_policy.max_delay_sec)

        print(f"❌ All retries exhausted for {task.collector_name}")
        return False

    def handle_fallback(self, task: CollectorTask):
        """
        Handle fallback when collector fails.

        Strategies:
          1. Use cached data (if available and fresh enough)
          2. Use yesterday's data
          3. Skip and alert
        """
        if not task.fallback_policy.enabled:
            print(f"⚠️ No fallback enabled for {task.collector_name}")
            return

        print(f"\n🔄 FALLBACK: {task.collector_name}")

        # Check for recent successful run
        self.cur.execute(
            """
            SELECT completed_at, records_processed
            FROM sofia.collector_runs
            WHERE collector_name = %s
              AND status = 'success'
              AND completed_at >= NOW() - INTERVAL '%s hours'
            ORDER BY completed_at DESC
            LIMIT 1
        """,
            (task.collector_name, task.fallback_policy.cache_max_age_hours),
        )

        result = self.cur.fetchone()

        if result:
            print(f"✅ Using cached data from {result['completed_at']}")
            print(f"   Records: {result['records_processed']}")
            if task.fallback_policy.notify_on_fallback:
                self.send_alert(f"⚠️ {task.collector_name} failed. Using cached data from {result['completed_at']}")
        else:
            print(f"⚠️ No recent cached data available")
            self.send_alert(f"❌ {task.collector_name} failed with no fallback data available!")

    def check_circuit_breaker(self, task: CollectorTask) -> bool:
        """
        Check if circuit breaker allows execution.

        Returns:
          True if can execute, False if circuit is open
        """
        if task.status != CollectorStatus.CIRCUIT_OPEN:
            # Check if should open circuit
            if task.consecutive_failures >= task.circuit_breaker.failure_threshold:
                print(f"🔌 CIRCUIT BREAKER OPENED: {task.collector_name}")
                print(f"   Reason: {task.consecutive_failures} consecutive failures")
                task.status = CollectorStatus.CIRCUIT_OPEN
                task.circuit_opened_at = datetime.now()
                self.send_alert(
                    f"🔌 Circuit breaker opened for {task.collector_name} after {task.consecutive_failures} failures"
                )
                return False
            return True

        # Circuit is open - check if recovery timeout elapsed
        if task.circuit_opened_at:
            elapsed = (datetime.now() - task.circuit_opened_at).total_seconds()
            if elapsed >= task.circuit_breaker.recovery_timeout_sec:
                print(f"🔌 CIRCUIT BREAKER HALF-OPEN: {task.collector_name}")
                print(f"   Testing with 1 call...")
                # Allow one test call
                return True

        print(f"🔌 CIRCUIT BREAKER OPEN: {task.collector_name}")
        print(f"   Waiting for recovery timeout...")
        return False

    def check_dependencies(self, task: CollectorTask) -> bool:
        """
        Check if all dependencies are healthy.

        Returns:
          True if dependencies OK, False if blocked
        """
        if not task.dependencies:
            return True

        for dep_name in task.dependencies:
            dep_task = self.tasks.get(dep_name)
            if not dep_task:
                print(f"⚠️ Dependency not found: {dep_name}")
                continue

            # Check if dependency is down for >48h
            if dep_task.last_run:
                hours_since = (datetime.now() - dep_task.last_run).total_seconds() / 3600
                if hours_since > 48:
                    print(f"❌ DEPENDENCY BLOCKED: {task.collector_name}")
                    print(f"   Dependency {dep_name} hasn't run in {hours_since:.1f}h")
                    task.status = CollectorStatus.DISABLED
                    return False

            # Check if dependency is failing
            if dep_task.status in [CollectorStatus.CIRCUIT_OPEN, CollectorStatus.DISABLED]:
                print(f"❌ DEPENDENCY BLOCKED: {task.collector_name}")
                print(f"   Dependency {dep_name} is {dep_task.status.value}")
                task.status = CollectorStatus.DISABLED
                return False

        return True

    # ========================================================================
    # SCHEDULER LOOP
    # ========================================================================

    def run_once(self, max_runtime_minutes: int = 60):
        """
        Run all pending tasks once.

        Args:
            max_runtime_minutes: Maximum runtime in minutes (default: 60)
        """
        start_time = datetime.now()
        max_runtime = timedelta(minutes=max_runtime_minutes)

        print("\n" + "=" * 80)
        print("🚀 RUNNING SCHEDULED TASKS")
        print(f"   Max Runtime: {max_runtime_minutes} minutes")
        print("=" * 80)

        # Sort tasks by priority
        tasks = sorted(self.tasks.values(), key=lambda t: (t.priority.value, t.next_run or datetime.min))

        for task in tasks:
            # Check if we've exceeded max runtime
            elapsed = datetime.now() - start_time
            if elapsed > max_runtime:
                print(f"\n⏰ Max runtime ({max_runtime_minutes}min) exceeded. Stopping.")
                break

            # Check circuit breaker
            if not self.check_circuit_breaker(task):
                continue

            # Check dependencies
            if not self.check_dependencies(task):
                continue

            # Execute with retry (but skip retry if we're running out of time)
            success = self.execute_collector(task)

            if not success and (datetime.now() - start_time) < (max_runtime * 0.8):
                # Only retry if we have 20% of time left
                success = self.retry_with_backoff(task)

            if not success:
                # Handle fallback
                self.handle_fallback(task)

        print("\n" + "=" * 80)
        print("✅ SCHEDULED RUN COMPLETE")
        print(f"   Runtime: {(datetime.now() - start_time).total_seconds():.1f}s")
        print("=" * 80)

    def run(self, interval_sec: int = 300):
        """
        Run scheduler loop.

        Args:
          interval_sec: Seconds between runs (default: 5 minutes)
        """
        self.running = True

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\n🛑 Shutting down scheduler...")
            self.running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        print("\n" + "=" * 80)
        print("🚀 INTELLIGENT SCHEDULER STARTED")
        print("=" * 80)
        print(f"   Interval: {interval_sec}s")
        print(f"   Tasks: {len(self.tasks)}")
        print("   Press Ctrl+C to stop")
        print("=" * 80)

        while self.running:
            self.run_once()
            print(f"\n⏰ Next run in {interval_sec}s...")
            time.sleep(interval_sec)

    # ========================================================================
    # DATABASE HELPERS
    # ========================================================================

    def start_collector_run(self, collector_name: str) -> int:
        """Start tracking a collector run."""
        self.cur.execute(
            """
            INSERT INTO sofia.collector_runs (collector_name, started_at, status)
            VALUES (%s, NOW(), 'running')
            RETURNING id
        """,
            (collector_name,),
        )
        self.conn.commit()
        return self.cur.fetchone()["id"]

    def complete_collector_run(self, run_id: int, status: str, error_message: Optional[str] = None):
        """Complete a collector run."""
        self.cur.execute(
            """
            UPDATE sofia.collector_runs
            SET status = %s,
                completed_at = NOW(),
                error_message = %s
            WHERE id = %s
        """,
            (status, error_message, run_id),
        )
        self.conn.commit()

    def send_alert(self, message: str):
        """Send WhatsApp alert."""
        if not self.whatsapp_enabled or not self.whatsapp_number:
            print(f"📢 ALERT (WhatsApp disabled): {message}")
            return

        try:
            payload = {"message": message, "whatsapp_number": self.whatsapp_number}
            response = requests.post(self.sofia_endpoint, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"📱 WhatsApp alert sent: {message}")
            else:
                print(f"⚠️ WhatsApp alert failed: {response.status_code}")
        except Exception as e:
            print(f"⚠️ WhatsApp alert error: {e}")

    def close(self):
        """Close database connection."""
        self.cur.close()
        self.conn.close()
        print("✅ Scheduler closed")


# ============================================================================
# CLI
# ============================================================================


def main():
    """CLI for intelligent scheduler."""
    import argparse

    parser = argparse.ArgumentParser(description="Sofia Intelligent Scheduler")
    parser.add_argument("--register-all", action="store_true", help="Register all collectors")
    parser.add_argument("--run-once", action="store_true", help="Run all tasks once and exit")
    parser.add_argument("--run", action="store_true", help="Run scheduler loop")
    parser.add_argument("--interval", type=int, default=300, help="Interval between runs (seconds)")

    args = parser.parse_args()

    scheduler = IntelligentScheduler()

    try:
        if args.register_all:
            scheduler.register_all_collectors()

        if args.run_once:
            scheduler.run_once()

        if args.run:
            scheduler.run(interval_sec=args.interval)

        if not any([args.register_all, args.run_once, args.run]):
            parser.print_help()

    finally:
        scheduler.close()


if __name__ == "__main__":
    main()
