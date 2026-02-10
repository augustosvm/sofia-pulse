#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sofia Skills Kit - Sync Expected Set
Sincroniza config/daily_expected_collectors.json com inventory (aplicando denylist).
"""

import sys
import json
import fnmatch
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.skill_runner import run


def matches_pattern(text, pattern):
    """Verifica se text match pattern (wildcard * permitido)."""
    return fnmatch.fnmatch(text, pattern)


def is_blocked(collector_id, path, denylist):
    """Verifica se collector está bloqueado pela denylist."""
    # 1. Allowlist tem precedência (sempre permitido)
    for allow_pattern in denylist.get("allow_collectors", []):
        if matches_pattern(collector_id, allow_pattern):
            return False  # Permitido explicitamente

    # 2. Verificar blocked_collectors
    for blocked_pattern in denylist.get("blocked_collectors", []):
        if matches_pattern(collector_id, blocked_pattern):
            return True

    # 3. Verificar blocked_paths_contains
    for blocked_substring in denylist.get("blocked_paths_contains", []):
        if blocked_substring in path.lower():
            return True

    return False  # Não bloqueado


def categorize_collector(collector_id):
    """Categoriza collector em grupo."""
    cid_lower = collector_id.lower()

    if cid_lower.startswith("ga4"):
        return "ga4"
    elif any(x in cid_lower for x in ["github", "hackernews", "npm", "pypi", "cybersecurity"]):
        return "tech"
    elif any(x in cid_lower for x in ["openalex", "research", "arxiv"]):
        return "research"
    elif "job" in cid_lower:
        return "jobs"
    elif "patent" in cid_lower:
        return "patents"
    else:
        return "other"


def main():
    print("[sync_expected_set] Starting sync...")

    project_root = Path(__file__).resolve().parents[1]
    denylist_path = project_root / "config" / "collector_denylist.json"
    output_path = project_root / "config" / "daily_expected_collectors.json"

    # 1. Carregar denylist
    if not denylist_path.exists():
        print(f"[sync_expected_set] ❌ Denylist not found: {denylist_path}")
        sys.exit(1)

    with open(denylist_path, "r") as f:
        denylist = json.load(f)

    print(f"[sync_expected_set] Loaded denylist:")
    print(f"  - Blocked collectors: {denylist.get('blocked_collectors', [])}")
    print(f"  - Blocked paths: {denylist.get('blocked_paths_contains', [])}")
    print(f"  - Allowed (override): {denylist.get('allow_collectors', [])}")

    # 2. Listar collectors ativos do inventory
    result = run("inventory.collectors", {"action": "list", "status": "active"})

    if not result["ok"]:
        print(f"[sync_expected_set] ❌ Failed to list inventory: {result['errors']}")
        sys.exit(1)

    all_collectors = result["data"]["collectors"]
    print(f"\n[sync_expected_set] Found {len(all_collectors)} active collectors in inventory")

    # 3. Filtrar com denylist
    allowed = []
    blocked = []

    for collector in all_collectors:
        cid = collector["collector_id"]
        path = collector.get("path", "")

        if is_blocked(cid, path, denylist):
            blocked.append({"collector_id": cid, "path": path})
        else:
            allowed.append(collector)

    print(f"\n[sync_expected_set] Filtering results:")
    print(f"  ✅ Allowed: {len(allowed)}")
    print(f"  ❌ Blocked: {len(blocked)}")

    if blocked:
        print(f"\n[sync_expected_set] Blocked collectors:")
        for b in blocked[:10]:  # Mostrar primeiros 10
            print(f"    - {b['collector_id']} (path: {b['path']})")
        if len(blocked) > 10:
            print(f"    ... and {len(blocked) - 10} more")

    # 4. Definir collectors required
    REQUIRED_IDS = ["bacen-sgs", "ibge-api", "ipea-api"]

    # 5. Categorizar e criar estrutura
    groups = {
        "required": [],
        "ga4": [],
        "tech": [],
        "research": [],
        "jobs": [],
        "patents": [],
        "other": []
    }

    for collector in allowed:
        cid = collector["collector_id"]

        # Determinar grupo
        if cid in REQUIRED_IDS:
            group = "required"
        else:
            group = categorize_collector(cid)

        # Determinar configuração
        is_required = (cid in REQUIRED_IDS) or (group == "ga4")
        timeout_s = 900 if group == "ga4" else 300

        groups[group].append({
            "collector_id": cid,
            "required": is_required,
            "timeout_s": timeout_s,
            "expected_min": collector.get("expected_min_records", 1),
            "allow_empty": collector.get("allow_empty", False)
        })

    # 6. Gerar config final
    config = {
        "_comment": "Expected set sincronizado automaticamente via sync_expected_set.py",
        "_generated_at": str(Path(__file__).stat().st_mtime),
        "_stats": {
            "total_allowed": len(allowed),
            "total_blocked": len(blocked),
            "required_count": len(groups["required"]) + len(groups["ga4"]),
            "groups": {k: len(v) for k, v in groups.items() if v}
        },
        "groups": {k: v for k, v in groups.items() if v}  # Apenas grupos não-vazios
    }

    # 7. Salvar
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n[sync_expected_set] ✅ Config saved to: {output_path}")
    print(f"\n[sync_expected_set] Groups summary:")
    for group_name, collectors in config["groups"].items():
        required_count = sum(1 for c in collectors if c.get("required", False))
        print(f"  - {group_name}: {len(collectors)} collectors ({required_count} required)")

    # 8. Gerar lista simples de collector_ids para backward compatibility
    all_collector_ids = []
    for collectors in config["groups"].values():
        all_collector_ids.extend([c["collector_id"] for c in collectors])

    # Criar versão legacy
    legacy_config = {
        "_comment": "Legacy format (deprecated, use groups instead)",
        "collectors": all_collector_ids
    }

    legacy_path = project_root / "config" / "daily_expected_collectors_legacy.json"
    with open(legacy_path, "w") as f:
        json.dump(legacy_config, f, indent=2)

    print(f"\n[sync_expected_set] ✅ Legacy config saved to: {legacy_path}")
    print(f"[sync_expected_set] Total collectors in expected set: {len(all_collector_ids)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
