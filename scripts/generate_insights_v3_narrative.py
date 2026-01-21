# scripts/generate_insights_v3_narrative.py
"""
Sofia Insight Engine V3 Plus - Narrative Edition
Integrates: data collection + rules + cross-LLM debate + validation + logging
"""
import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv

# Add scripts to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_insights_v3_plus import (
    DB_CONFIG, OUTPUT_DIR, RULES_FILE,
    DecimalEncoder, fetch_sql, fetch_all_metrics, load_rules,
    rule_passes, insight_is_valid, select_top_insights, get_build_info
)
from narrative_generator import (
    generate_narrative_for_insight, enrich_insight_with_narrative
)
from narrative_validator import validate_narrative, ValidationResult

load_dotenv()

PIPELINE_VERSION = "v3plus-narrative-1"
REJECTIONS_DIR = "public/insights"


def log_rejection(
    insight: Dict[str, Any],
    result: ValidationResult,
    log_file: str
) -> None:
    """Log a rejected narrative to JSONL file"""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "id": insight.get("id"),
        "domain": insight.get("domain"),
        "headline": insight.get("headline", "")[:100],
        "reasons": result.reasons,
        "flags": result.flags,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def enrich_and_validate_insights(
    insights: List[Dict[str, Any]],
    ready_flags: Dict[str, int],
    log_file: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Enrich insights with narratives and validate them.
    
    Returns:
        (passed_insights, blocked_insights)
    """
    passed = []
    blocked = []
    
    for insight in insights:
        insight_id = insight.get("id", "unknown")
        
        # Step 1: Generate narrative using cross-LLM debate
        try:
            narrative = await generate_narrative_for_insight(insight)
            enriched = enrich_insight_with_narrative(insight, narrative)
        except Exception as e:
            print(f"   [ERROR] Narrative generation failed for {insight_id}: {e}")
            enriched = dict(insight)
            enriched["narrative"] = {"status": "blocked", "error": str(e)}
            enriched["narrative_score"] = {"depth": 0, "clarity": 0, "actionability": 0, "veracity": 0}
            blocked.append(enriched)
            continue
        
        # Step 2: Validate narrative
        validation_result = validate_narrative(enriched, ready_flags)
        enriched["narrative_validation"] = validation_result.to_dict()
        
        # Step 3: Route based on validation
        if validation_result.passed and enriched.get("narrative", {}).get("status") == "ok":
            passed.append(enriched)
        else:
            # Log rejection
            log_rejection(insight, validation_result, log_file)
            
            # Mark as blocked but keep in output
            if enriched.get("narrative", {}).get("status") != "blocked":
                enriched["narrative"]["status"] = "blocked"
            blocked.append(enriched)
    
    return passed, blocked


async def run_narrative_pipeline():
    """Main pipeline execution with narrative enrichment"""
    print("=" * 60)
    print(f"Sofia Insight Engine {PIPELINE_VERSION}")
    print("=" * 60)
    
    generated_at = datetime.now(timezone.utc).isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"{REJECTIONS_DIR}/narrative_rejections_{today}.jsonl"
    
    # Step 1: Load rules and metrics (reuse from v3_plus)
    print("\n[1/6] Loading rules and metrics...")
    rules = load_rules()
    print(f"   Loaded {len(rules)} rules")
    
    print("\n[2/6] Fetching metrics from database...")
    metrics, kpis, drivers, status = fetch_all_metrics()
    
    ready_flags = {k: v for k, v in metrics.items() if k.endswith("_ready")}
    print(f"   Ready flags: {ready_flags}")
    
    # Step 2: Apply rules to generate raw insights
    print("\n[3/6] Applying rules...")
    raw_insights = []
    for rule in rules:
        if rule_passes(rule, metrics):
            insight = format_insight(rule, metrics)
            if insight_is_valid(rule, insight.get("evidence", []), metrics):
                raw_insights.append(insight)
    
    print(f"   Raw insights: {len(raw_insights)}")
    
    # Step 3: Select top insights (curated)
    print("\n[4/6] Curating with domain/family caps...")
    curated = select_top_insights(raw_insights)
    print(f"   Curated insights: {len(curated)}")
    
    # Step 4: Enrich with narratives and validate
    print("\n[5/6] Generating narratives (cross-LLM debate)...")
    passed, blocked = await enrich_and_validate_insights(curated, ready_flags, log_file)
    print(f"   Passed: {len(passed)}, Blocked: {len(blocked)}")
    
    # Step 5: Build output
    print("\n[6/6] Building output...")
    build_info = get_build_info()
    build_info["pipeline_version"] = PIPELINE_VERSION
    
    # Sort passed insights by priority and narrative score
    def sort_key(i):
        ns = i.get("narrative_score", {})
        return (
            -i.get("priority", 0),
            -ns.get("depth", 0),
            -ns.get("actionability", 0)
        )
    passed.sort(key=sort_key)
    
    output = {
        "generated_at": generated_at,
        "meta": {
            "build": build_info,
            "kpis": kpis,
            "ready": ready_flags,
            "status": status,
            "narrative_stats": {
                "passed": len(passed),
                "blocked": len(blocked),
                "total": len(curated),
            },
            "notes": [
                "Narratives generated via cross-LLM debate (4 minis + Gemini synthesis).",
                "Validated with anti-zero + anti-hallucination + grounding checks."
            ],
        },
        "drivers": drivers,
        "top_insights": passed,
        "blocked_insights": blocked,
        "health": [],
        "insights": passed + blocked,
    }
    
    # Save output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in ["today.json", "today_v3_narrative.json"]:
        with open(f"{OUTPUT_DIR}/{filename}", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
    
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete: {len(passed)} insights with narratives")
    print(f"Blocked: {len(blocked)} (see {log_file})")
    print(f"Output: {OUTPUT_DIR}/today.json")
    print(f"{'=' * 60}")
    
    return output


def format_insight(rule: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Format a rule into an insight with populated values"""
    headline = rule.get("headline", "")
    summary = rule.get("summary", "")
    
    # Format placeholders
    try:
        headline = headline.format(**metrics)
    except (KeyError, ValueError):
        pass
    try:
        summary = summary.format(**metrics)
    except (KeyError, ValueError):
        pass
    
    # Build evidence
    evidence = []
    for ev in rule.get("evidence", []):
        metric_name = ev.get("metric")
        value = metrics.get(metric_name)
        evidence.append({
            "metric": metric_name,
            "value": value,
        })
    
    return {
        "id": rule.get("id"),
        "domain": rule.get("domain"),
        "category": rule.get("category"),
        "family": rule.get("family", "general"),
        "severity": rule.get("severity"),
        "priority": rule.get("priority"),
        "valid_for_hours": rule.get("valid_for_hours"),
        "headline": headline,
        "summary": summary,
        "evidence": evidence,
        "why_it_matters": rule.get("why_it_matters", ""),
        "actions": rule.get("actions", []),
        "confidence": rule.get("confidence", 0.7),
    }


if __name__ == "__main__":
    asyncio.run(run_narrative_pipeline())
