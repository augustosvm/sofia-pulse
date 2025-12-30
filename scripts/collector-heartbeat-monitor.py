#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
SOFIA PULSE - COLLECTOR HEARTBEAT MONITOR
════════════════════════════════════════════════════════════════════════════════

Monitors collector health and sends WhatsApp alerts when:
- Collector hasn't run in >12 hours
- Collector failed >3 times in 24h
- Success rate drops below 80%

Run via cron every hour:
0 * * * * cd /home/ubuntu/sofia-pulse && python3 scripts/collector-heartbeat-monitor.py
"""

import os
from datetime import datetime

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


class CollectorHeartbeatMonitor:
    """Monitor collector health and send alerts"""

    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            user=os.getenv("POSTGRES_USER", "sofia"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB", "sofia_db"),
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

        # WhatsApp config
        self.whatsapp_enabled = os.getenv("ALERT_WHATSAPP_ENABLED", "true").lower() == "true"
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER")
        self.sofia_endpoint = os.getenv("SOFIA_API_ENDPOINT", "http://localhost:8001/api/v2/chat")

        # Alert thresholds
        self.max_hours_silence = 12
        self.min_success_rate = 80.0
        self.max_failures_24h = 3

        self.alerts = []

    def check_stale_collectors(self):
        """Check for collectors that haven't run recently"""
        self.cur.execute(
            """
            SELECT 
                collector_name,
                MAX(completed_at) as last_run,
                EXTRACT(EPOCH FROM (NOW() - MAX(completed_at))) / 3600 as hours_since_last_run
            FROM sofia.collector_runs
            WHERE completed_at IS NOT NULL
            GROUP BY collector_name
            HAVING MAX(completed_at) < NOW() - INTERVAL '%s hours'
            ORDER BY last_run ASC
        """
            % self.max_hours_silence
        )

        stale = self.cur.fetchall()

        for collector in stale:
            hours = int(collector["hours_since_last_run"])
            self.alerts.append(
                {
                    "type": "STALE_COLLECTOR",
                    "severity": "HIGH" if hours > 24 else "MEDIUM",
                    "collector": collector["collector_name"],
                    "message": f"🔴 {collector['collector_name']} hasn't run in {hours}h (last: {collector['last_run']})",
                    "data": collector,
                }
            )

    def check_failing_collectors(self):
        """Check for collectors with high failure rates"""
        self.cur.execute(
            """
            SELECT 
                collector_name,
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
            FROM sofia.collector_runs
            WHERE started_at >= NOW() - INTERVAL '24 hours'
            GROUP BY collector_name
            HAVING 
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) >= %s
                OR
                (COUNT(*) >= 3 AND 100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*) < %s)
            ORDER BY success_rate ASC
        """
            % (self.max_failures_24h, self.min_success_rate)
        )

        failing = self.cur.fetchall()

        for collector in failing:
            if collector["failed_runs"] >= self.max_failures_24h:
                self.alerts.append(
                    {
                        "type": "HIGH_FAILURE_RATE",
                        "severity": "HIGH",
                        "collector": collector["collector_name"],
                        "message": f"🔴 {collector['collector_name']} failed {collector['failed_runs']} times in 24h (success rate: {collector['success_rate']}%)",
                        "data": collector,
                    }
                )
            elif collector["success_rate"] < self.min_success_rate:
                self.alerts.append(
                    {
                        "type": "LOW_SUCCESS_RATE",
                        "severity": "MEDIUM",
                        "collector": collector["collector_name"],
                        "message": f"🟡 {collector['collector_name']} success rate: {collector['success_rate']}% (threshold: {self.min_success_rate}%)",
                        "data": collector,
                    }
                )

    def check_running_too_long(self):
        """Check for collectors stuck in 'running' state"""
        self.cur.execute(
            """
            SELECT 
                collector_name,
                started_at,
                EXTRACT(EPOCH FROM (NOW() - started_at)) / 3600 as hours_running
            FROM sofia.collector_runs
            WHERE status = 'running'
              AND started_at < NOW() - INTERVAL '2 hours'
            ORDER BY started_at ASC
        """
        )

        stuck = self.cur.fetchall()

        for collector in stuck:
            hours = int(collector["hours_running"])
            self.alerts.append(
                {
                    "type": "STUCK_COLLECTOR",
                    "severity": "HIGH",
                    "collector": collector["collector_name"],
                    "message": f"🔴 {collector['collector_name']} stuck in 'running' state for {hours}h (started: {collector['started_at']})",
                    "data": collector,
                }
            )

    def get_failed_collectors_today(self):
        """Get collectors that failed today"""
        self.cur.execute(
            """
            SELECT * FROM sofia.failed_collectors_today
            WHERE failed_count > 0
        """
        )
        return self.cur.fetchall()

    def send_whatsapp_alert(self, message: str):
        """Send alert via WhatsApp using Sofia API"""
        if not self.whatsapp_enabled or not self.whatsapp_number:
            print(f"  ⚠️ WhatsApp alerts disabled")
            return False

        try:
            payload = {"message": message, "whatsapp_number": self.whatsapp_number}

            response = requests.post(self.sofia_endpoint, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"  ✓ WhatsApp alert sent")
                return True
            else:
                print(f"  ✗ WhatsApp alert failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"  ✗ WhatsApp alert error: {e}")
            return False

    def run(self):
        """Run all health checks"""
        print("\n" + "=" * 80)
        print("SOFIA PULSE - COLLECTOR HEARTBEAT MONITOR")
        print("=" * 80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Run checks
        print("\n🔍 Checking for stale collectors...")
        self.check_stale_collectors()

        print("🔍 Checking for failing collectors...")
        self.check_failing_collectors()

        print("🔍 Checking for stuck collectors...")
        self.check_running_too_long()

        # Report findings
        print(f"\n{'='*80}")
        print(f"HEALTH CHECK RESULTS")
        print(f"{'='*80}")
        print(f"Total alerts: {len(self.alerts)}")

        if not self.alerts:
            print("✅ All collectors healthy!")
            return

        # Group by severity
        high = [a for a in self.alerts if a["severity"] == "HIGH"]
        medium = [a for a in self.alerts if a["severity"] == "MEDIUM"]

        print(f"  HIGH severity: {len(high)}")
        print(f"  MEDIUM severity: {len(medium)}")

        print(f"\n{'='*80}")
        print(f"ALERT DETAILS")
        print(f"{'='*80}")

        for alert in self.alerts:
            print(f"\n[{alert['severity']}] {alert['type']}")
            print(f"  {alert['message']}")

        # Send WhatsApp alert if there are HIGH severity issues
        if high:
            alert_msg = f"🚨 SOFIA PULSE ALERT\n\n"
            alert_msg += f"{len(high)} collector(s) need attention:\n\n"

            for alert in high[:5]:  # Limit to 5
                alert_msg += f"• {alert['message']}\n"

            if len(high) > 5:
                alert_msg += f"\n... and {len(high) - 5} more issues"

            print(f"\n{'='*80}")
            print(f"SENDING WHATSAPP ALERT")
            print(f"{'='*80}")
            self.send_whatsapp_alert(alert_msg)

        print(f"\n{'='*80}\n")

    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    monitor = CollectorHeartbeatMonitor()
    try:
        monitor.run()
    finally:
        monitor.close()
