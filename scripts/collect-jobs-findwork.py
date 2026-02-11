#!/usr/bin/env python3
"""
Wrapper for collect-jobs-findwork.ts
Executes TypeScript collector via tsx
"""
import sys
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def main():
    script_dir = Path(__file__).parent
    ts_script = script_dir / "collect-jobs-findwork.ts"

    if not ts_script.exists():
        print(f"❌ ERROR: SCRIPT_NOT_FOUND - collect-jobs-findwork.ts")
        sys.exit(1)

    # Check tsx
    try:
        subprocess.run(["npx", "tsx", "--version"],
                      capture_output=True, check=True, timeout=5)
    except Exception:
        print("❌ ERROR: DEPENDENCY_MISSING - tsx not installed")
        sys.exit(1)

    # Execute TypeScript
    try:
        result = subprocess.run(
            ["npx", "tsx", str(ts_script)],
            timeout=300,
            env=os.environ.copy()
        )
        sys.exit(result.returncode)

    except subprocess.TimeoutExpired:
        print("❌ ERROR: TIMEOUT")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: UNKNOWN - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
