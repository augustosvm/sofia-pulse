"""Sofia Pulse — Filesystem Bootstrap

Garante que diretórios necessários existem.
Se /var/log/sofia não for gravável, cai para /tmp/sofia.
"""

import os
from pathlib import Path


def ensure_directories():
    """Cria diretórios necessários com fallback.

    Retorna:
        dict: {"log_dir": Path, "warnings": [str]}
    """
    warnings = []

    # 1. Determinar SOFIA_LOG_DIR
    preferred = Path("/var/log/sofia")
    fallback = Path("/tmp/sofia")

    log_dir_env = os.getenv("SOFIA_LOG_DIR")
    if log_dir_env:
        log_dir = Path(log_dir_env)
    else:
        # Tentar criar /var/log/sofia
        try:
            preferred.mkdir(parents=True, exist_ok=True)
            log_dir = preferred
        except (PermissionError, OSError):
            # Fallback para /tmp/sofia
            fallback.mkdir(parents=True, exist_ok=True)
            log_dir = fallback
            warnings.append(f"Cannot write to {preferred}, using {fallback}")

    # 2. Criar subdiretórios
    collectors_dir = log_dir / "collectors"
    try:
        collectors_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        warnings.append(f"Cannot create {collectors_dir}: {e}")

    return {
        "log_dir": str(log_dir),
        "collectors_dir": str(collectors_dir),
        "warnings": warnings
    }
