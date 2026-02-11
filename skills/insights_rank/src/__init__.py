"""Sofia Skill: insights.rank — Ranking determinístico por 4 dimensões. Sem LLM."""

import time
from datetime import datetime, timezone, timedelta
from lib.helpers import ok, fail

DEFAULTS = {"impact": 0.3, "novelty": 0.3, "credibility": 0.2, "coverage": 0.2}
TYPE_BOOST = {"security_event": 0.2, "capital_deal": 0.15, "ipo": 0.1, "job_posting": 0.05, "research_paper": 0.05}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        insights = params.get("insights", [])
        w = {**DEFAULTS, **(params.get("weights") or {})}
        top_k = params.get("top_k", 10)
        since = params.get("since_days", 7)
        if not insights:
            return fail("INSUFFICIENT_DATA", "No insights to rank", start)

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=since)
        scored = []

        for item in insights:
            s = {"impact": _impact(item), "novelty": _novelty(item, cutoff, now),
                 "credibility": _cred(item), "coverage": _cov(item)}
            total = sum(s[k] * w[k] for k in s)
            scored.append({**item, "score": round(total, 4), "scores": {k: round(v, 4) for k, v in s.items()}})

        scored.sort(key=lambda x: x["score"], reverse=True)
        for i, item in enumerate(scored): item["rank"] = i + 1

        return ok({"ranked": scored[:top_k], "total_evaluated": len(insights), "weights_used": w}, start)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _impact(item):
    sev = item.get("severity", 0)
    base = min(float(sev) / 10, 1.0) if isinstance(sev, (int, float)) else 0.5
    return min(base + TYPE_BOOST.get(item.get("entity_type", ""), 0), 1.0)

def _novelty(item, cutoff, now):
    ds = item.get("event_date") or item.get("normalized_at") or item.get("ingested_at")
    if not ds: return 0.5
    try:
        dt = datetime.fromisoformat(ds.replace("Z", "+00:00")) if "T" in str(ds) else datetime.strptime(str(ds)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if dt < cutoff: return 0.0
        w = (now - cutoff).total_seconds()
        return max(0, 1.0 - (now - dt).total_seconds() / w) if w > 0 else 0.5
    except: return 0.5

def _cred(item):
    c = item.get("confidence")
    if c is not None: return min(float(c), 1.0)
    n = len(item.get("sources", []))
    return 0.9 if n >= 3 else 0.7 if n == 2 else 0.5 if n == 1 else 0.3

def _cov(item):
    return min(len(set(item.get("sources", []))) / 4, 1.0)
