#!/usr/bin/env python3
"""WhatsApp Notifier - Send alerts and reports"""

import os

import requests


class WhatsAppNotifier:
    def __init__(self):
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER", "5527988024062")
        self.whatsapp_api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:3001/send")
        self.enabled = os.getenv("WHATSAPP_ENABLED", "true").lower() == "true"

    def send(self, message: str) -> bool:
        """Send WhatsApp message"""
        if not self.enabled:
            return False

        try:
            response = requests.post(
                self.whatsapp_api_url, json={"to": self.whatsapp_number, "message": message}, timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def report_sent(self, reports_count: int, csvs_count: int, email_to: str):
        """Notify when email report is sent"""
        message = f"""✅ Sofia Pulse Report Sent

📧 Email: {email_to}
📄 Reports: {reports_count}
📊 CSVs: {csvs_count}

Check your email!"""
        self.send(message)

    def collector_error(self, collector_name: str, error: str):
        """Alert on collector failure"""
        message = f"""❌ Collector Failed

📦 Collector: {collector_name}
🔴 Error: {error}

Check logs!"""
        self.send(message)

    def analytics_error(self, analytics_name: str, error: str):
        """Alert on analytics failure"""
        message = f"""❌ Analytics Failed

📊 Analytics: {analytics_name}
🔴 Error: {error}

Check logs!"""
        self.send(message)

    def daily_summary(self, total_records: int, failed_collectors: list):
        """Send daily collection summary"""
        status = "✅" if not failed_collectors else "⚠️"
        failures = "\n".join([f"• {c}" for c in failed_collectors]) if failed_collectors else "None"

        message = f"""{status} Sofia Pulse Daily Summary

📊 Records collected: {total_records:,}
❌ Failed collectors: {len(failed_collectors)}

{failures}"""
        self.send(message)

    def send_report(self, report_path: str, max_chars: int = 4000):
        """Send analysis report via WhatsApp (truncated if needed)"""
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Truncate if too long
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n... (relatório completo no email)"

            self.send(content)
            return True
        except:
            return False
