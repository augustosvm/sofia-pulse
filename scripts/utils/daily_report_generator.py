#!/usr/bin/env python3
"""
Daily Report Generator - Analyze all collector logs and generate WhatsApp report
"""

import glob
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Add utils to path
sys.path.insert(0, os.path.dirname(__file__))
from error_analyzer import ErrorAnalyzer
from whatsapp_notifier import WhatsAppNotifier


class DailyReportGenerator:
    """Generate daily success/failure report from collector logs"""

    def __init__(self, log_dir: str = "/var/log/sofia"):
        self.log_dir = log_dir
        self.analyzer = ErrorAnalyzer()
        self.whatsapp = WhatsAppNotifier()
        self.today = datetime.now().strftime("%Y-%m-%d")

    def find_todays_logs(self) -> List[str]:
        """Find all log files from today"""
        log_patterns = [
            f"{self.log_dir}/*.log",
            f"{self.log_dir}/collectors/*.log",
            "./logs/sofia/*.log",
            "./logs/*.log",
        ]

        all_logs = []
        for pattern in log_patterns:
            all_logs.extend(glob.glob(pattern))

        # Filter for today's logs
        todays_logs = []
        for log_file in all_logs:
            # Check if file was modified today
            try:
                mtime = os.path.getmtime(log_file)
                file_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                if file_date == self.today:
                    todays_logs.append(log_file)
            except:
                pass

        return todays_logs

    def analyze_log_file(self, log_path: str) -> Tuple[str, bool, str, str]:
        """
        Analyze a single log file

        Returns:
            (collector_name, success, error_category, error_details)
        """
        collector_name = self.extract_collector_name(log_path)

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Check for success indicators
            if any(indicator in content for indicator in ["✅", "Success", "Complete", "Inserted"]):
                # But also check for errors
                if any(error in content.lower() for error in ["error", "failed", "exception", "❌"]):
                    # Has success but also errors - partial success
                    error_text = self.extract_error_from_log(content)
                    category, short_msg, details = self.analyzer.analyze_error(error_text)
                    return (collector_name, False, category, short_msg)
                else:
                    return (collector_name, True, "", "")

            # Check for failure indicators
            if any(indicator in content.lower() for indicator in ["error", "failed", "exception", "traceback"]):
                error_text = self.extract_error_from_log(content)
                category, short_msg, details = self.analyzer.analyze_error(error_text)
                return (collector_name, False, category, short_msg)

            # No clear indicators - assume success if file exists and has content
            if len(content) > 100:
                return (collector_name, True, "", "")
            else:
                return (collector_name, False, "Unknown", "Log file too small or empty")

        except Exception as e:
            return (collector_name, False, "Log Read Error", str(e))

    def extract_collector_name(self, log_path: str) -> str:
        """Extract collector name from log path"""
        filename = os.path.basename(log_path)
        # Remove .log extension and date suffix
        name = filename.replace(".log", "")
        name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", name)
        name = re.sub(r"-\d+$", "", name)  # Remove -2, -3 suffixes
        return name

    def extract_error_from_log(self, content: str) -> str:
        """Extract relevant error message from log content"""
        lines = content.split("\n")

        # Look for error patterns
        error_lines = []
        for i, line in enumerate(lines):
            if any(err in line.lower() for err in ["error:", "exception:", "traceback", "failed", "❌"]):
                # Get context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                error_lines.extend(lines[start:end])
                break

        if error_lines:
            return "\n".join(error_lines[-10:])  # Last 10 lines

        # If no specific error found, return last 20 lines
        return "\n".join(lines[-20:])

    def group_by_frequency(self, collectors: List[str]) -> Dict[str, List[str]]:
        """Group collectors by their expected frequency"""

        hourly = ["hackernews", "reddit", "npm", "pypi", "github-trending", "github-niches", "gdelt"]
        daily = [
            "bacen",
            "ibge",
            "ipea",
            "comexstat",
            "brazil-ministries",
            "brazil-security",
            "electricity",
            "energy-global",
            "commodities",
            "ports",
            "arxiv",
            "openalex",
            "nih",
            "epo",
            "wipo",
            "ai-regulation",
            "ai-companies",
            "cybersecurity",
            "space",
            "who",
            "unicef",
            "ilo",
            "un-sdg",
            "hdx",
            "wto",
            "fao",
            "cepal",
            "tourism",
            "world-security",
            "semiconductors",
            "cardboard",
            "hkex",
        ]
        weekly = ["women-", "sports-", "asia-universities", "central-banks-women"]
        monthly = ["socioeconomic", "religion", "ngos", "drugs", "wb-gender", "basedosdados"]

        groups = {"hourly": [], "daily": [], "weekly": [], "monthly": [], "other": []}

        for collector in collectors:
            collector_lower = collector.lower()
            if any(h in collector_lower for h in hourly):
                groups["hourly"].append(collector)
            elif any(d in collector_lower for d in daily):
                groups["daily"].append(collector)
            elif any(w in collector_lower for w in weekly):
                groups["weekly"].append(collector)
            elif any(m in collector_lower for m in monthly):
                groups["monthly"].append(collector)
            else:
                groups["other"].append(collector)

        return groups

    def generate_report(self) -> str:
        """Generate complete daily report"""

        print("🔍 Finding today's logs...")
        log_files = self.find_todays_logs()
        print(f"   Found {len(log_files)} log files from today")

        if not log_files:
            return "⚠️ No logs found for today"

        # Analyze all logs
        print("📊 Analyzing logs...")
        results = []
        for log_file in log_files:
            result = self.analyze_log_file(log_file)
            results.append(result)

        # Separate success and failures
        successes = [r for r in results if r[1]]
        failures = [r for r in results if not r[1]]

        total = len(results)
        success_count = len(successes)
        failure_count = len(failures)
        success_rate = (success_count / total * 100) if total > 0 else 0

        # Group failures by category
        failures_by_category = {}
        for name, _, category, msg in failures:
            if category not in failures_by_category:
                failures_by_category[category] = []
            failures_by_category[category].append((name, msg))

        # Build report
        status_emoji = "✅" if failure_count == 0 else ("⚠️" if failure_count < 5 else "❌")

        report = f"""{status_emoji} Sofia Pulse - Relatório Diário
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 RESUMO GERAL
━━━━━━━━━━━━━━━━
Total: {total} collectors
✅ Sucesso: {success_count} ({success_rate:.1f}%)
❌ Falhas: {failure_count}"""

        if failure_count > 0:
            report += f"\n\n🔴 FALHAS POR CATEGORIA\n━━━━━━━━━━━━━━━━"

            for category, items in sorted(failures_by_category.items()):
                report += f"\n\n{category} ({len(items)}):"
                for name, msg in items[:5]:  # Max 5 per category
                    report += f"\n• {name}"
                    if msg:
                        report += f"\n  {msg[:80]}"

                if len(items) > 5:
                    report += f"\n  ... e mais {len(items) - 5}"

        # Add success summary
        if success_count > 0:
            report += f"\n\n✅ SUCESSOS ({success_count})"
            report += f"\n━━━━━━━━━━━━━━━━"

            # Group successes by frequency
            success_names = [r[0] for r in successes]
            grouped = self.group_by_frequency(success_names)

            for freq, collectors in grouped.items():
                if collectors:
                    report += f"\n{freq.title()}: {len(collectors)}"

        # Add next steps if there are failures
        if failure_count > 0:
            report += f"\n\n📝 PRÓXIMOS PASSOS"
            report += f"\n━━━━━━━━━━━━━━━━"

            # Prioritize by category
            priority_categories = ["SQL: Missing Table", "SQL: Missing Column", "API: Missing/Invalid Key"]
            critical_failures = [cat for cat in priority_categories if cat in failures_by_category]

            if critical_failures:
                report += f"\n⚠️ CRÍTICO: Corrigir primeiro"
                for cat in critical_failures[:3]:
                    items = failures_by_category[cat]
                    report += f"\n• {cat}: {len(items)} collector(s)"

        report += f"\n\n📁 Logs: {self.log_dir}"

        return report

    def send_report(self):
        """Generate and send report via WhatsApp"""
        try:
            report = self.generate_report()
            print("\n" + "=" * 60)
            print("DAILY REPORT")
            print("=" * 60)
            print(report)
            print("=" * 60)

            # Split if too long (WhatsApp limit ~4000 chars)
            if len(report) > 3800:
                parts = self.split_report(report, 3800)
                for i, part in enumerate(parts):
                    if i > 0:
                        part = f"📄 Parte {i+1}/{len(parts)}\n\n" + part
                    success = self.whatsapp.send(part)
                    if success:
                        print(f"✅ Part {i+1} sent via WhatsApp")
                    else:
                        print(f"⚠️ Part {i+1} failed to send")
            else:
                success = self.whatsapp.send(report)
                if success:
                    print("✅ Report sent via WhatsApp")
                else:
                    print("⚠️ Failed to send via WhatsApp")

            return report

        except Exception as e:
            error_msg = f"❌ Error generating report: {e}"
            print(error_msg)
            self.whatsapp.send(error_msg)
            return None

    def split_report(self, report: str, max_chars: int) -> List[str]:
        """Split long report into multiple messages"""
        parts = []
        current = ""

        for line in report.split("\n"):
            if len(current) + len(line) + 1 > max_chars:
                parts.append(current)
                current = line + "\n"
            else:
                current += line + "\n"

        if current:
            parts.append(current)

        return parts


def main():
    """Main entry point"""
    # Check for log directory argument
    log_dir = sys.argv[1] if len(sys.argv) > 1 else "/var/log/sofia"

    # Also check common alternative locations
    if not os.path.exists(log_dir):
        alternatives = ["./logs/sofia", "./logs", "/var/log"]
        for alt in alternatives:
            if os.path.exists(alt):
                log_dir = alt
                break

    print(f"📁 Using log directory: {log_dir}")

    generator = DailyReportGenerator(log_dir)
    generator.send_report()


if __name__ == "__main__":
    main()
