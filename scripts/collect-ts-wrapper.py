#!/usr/bin/env python3
"""
TypeScript Collector Wrapper
Permite executar collectors .ts via tsx/node sem converter para Python
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def run_typescript_collector(script_path):
    """Executa um collector TypeScript e retorna resultado"""

    # Verificar se arquivo existe
    full_path = Path(__file__).parent / script_path
    if not full_path.exists():
        print(f"❌ ERROR: SCRIPT_NOT_FOUND - {script_path}")
        return {"ok": False, "error": "SCRIPT_NOT_FOUND", "saved": 0}

    # Verificar se tsx está instalado
    try:
        subprocess.run(["npx", "tsx", "--version"],
                      capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ ERROR: DEPENDENCY_MISSING - tsx not installed")
        print("   Install with: npm install -g tsx")
        return {"ok": False, "error": "DEPENDENCY_MISSING", "saved": 0}

    # Executar TypeScript com tsx
    try:
        print(f"🚀 Running TypeScript: {script_path}")

        # Timeout de 5 minutos
        result = subprocess.run(
            ["npx", "tsx", str(full_path)],
            capture_output=True,
            text=True,
            timeout=300,
            env=os.environ.copy()
        )

        # Mostrar output
        if result.stdout:
            print(result.stdout)

        if result.stderr and result.returncode != 0:
            print(result.stderr, file=sys.stderr)

        # Interpretar exit code
        if result.returncode == 0:
            # Tentar extrair número de registros salvos do output
            saved = 0
            for line in result.stdout.split('\n'):
                if 'saved' in line.lower() or 'collected' in line.lower():
                    # Tentar extrair número
                    import re
                    numbers = re.findall(r'(\d+)', line)
                    if numbers:
                        saved = int(numbers[-1])  # Último número encontrado
                        break

            return {"ok": True, "saved": saved, "fetched": 0}
        else:
            # Exit code != 0 - erro
            error_code = "SCRIPT_ERROR"

            # Tentar identificar erro específico
            stderr_lower = result.stderr.lower()
            if "auth" in stderr_lower or "401" in stderr_lower or "403" in stderr_lower:
                error_code = "AUTH_MISSING"
            elif "timeout" in stderr_lower or "timed out" in stderr_lower:
                error_code = "TIMEOUT"
            elif "rate" in stderr_lower or "429" in stderr_lower:
                error_code = "RATE_LIMIT"
            elif "not found" in stderr_lower or "enoent" in stderr_lower:
                error_code = "DEPENDENCY_MISSING"

            return {"ok": False, "error": error_code, "saved": 0}

    except subprocess.TimeoutExpired:
        print("❌ ERROR: TIMEOUT - Script exceeded 5 minutes")
        return {"ok": False, "error": "TIMEOUT", "saved": 0}

    except Exception as e:
        print(f"❌ ERROR: UNKNOWN - {str(e)}")
        return {"ok": False, "error": "UNKNOWN", "saved": 0}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 collect-ts-wrapper.py <script_path>")
        print("Example: python3 collect-ts-wrapper.py collect-jobs-linkedin.ts")
        sys.exit(1)

    script_path = sys.argv[1]
    result = run_typescript_collector(script_path)

    # Output JSON para parsing
    print(f"\n📊 RESULT: {json.dumps(result)}")

    # Exit code
    sys.exit(0 if result["ok"] else 1)
