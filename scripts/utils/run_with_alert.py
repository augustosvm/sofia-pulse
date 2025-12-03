#!/usr/bin/env python3
"""Wrapper to run collectors/analytics with WhatsApp alerts on failure"""

import sys
import subprocess
import os

sys.path.insert(0, os.path.dirname(__file__))
try:
    from whatsapp_notifier import WhatsAppNotifier
    whatsapp = WhatsAppNotifier()
except:
    whatsapp = None

def run_command(cmd: list, name: str):
    """Run command and alert on failure"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            error = result.stderr or result.stdout or "Unknown error"
            if whatsapp:
                whatsapp.collector_error(name, error[:200])
            print(f"❌ {name} failed: {error}", file=sys.stderr)
            return False

        return True

    except subprocess.TimeoutExpired:
        if whatsapp:
            whatsapp.collector_error(name, "Timeout after 10 minutes")
        print(f"❌ {name} timeout", file=sys.stderr)
        return False

    except Exception as e:
        if whatsapp:
            whatsapp.collector_error(name, str(e))
        print(f"❌ {name} error: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: run_with_alert.py <name> <command> [args...]")
        sys.exit(1)

    name = sys.argv[1]
    cmd = sys.argv[2:]

    success = run_command(cmd, name)
    sys.exit(0 if success else 1)
