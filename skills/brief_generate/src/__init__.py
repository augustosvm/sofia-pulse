"""Sofia Skill: brief.generate — Brief executivo com citações. LLM cascade Gemini→Anthropic."""

import os, time, json, requests
from lib.helpers import ok, fail

LLM = {
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
               "key": "GEMINI_API_KEY", "model": "gemini-2.0-flash", "cost_1k": 0.0},
    "anthropic": {"url": "https://api.anthropic.com/v1/messages",
                  "key": "ANTHROPIC_API_KEY", "model": "claude-sonnet-4-20250514", "cost_1k": 0.003},
    "openai": {"url": "https://api.openai.com/v1/chat/completions",
               "key": "OPENAI_API_KEY", "model": "gpt-4o-mini", "cost_1k": 0.00015},
}
STYLES = {
    "professional": "Escreva de forma executiva, direta, factual.",
    "neutral": "Escreva de forma neutra e informativa.",
    "sofia_sarcastic": "Perspicaz, levemente sarcástica, sempre fundamentada em dados.",
}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        topic = params.get("topic", "")
        insights = params.get("insights", [])
        signals = params.get("signals", [])
        style = params.get("style_profile", "professional")
        max_len = params.get("max_length", 1500)
        lang = params.get("language", "pt-BR")
        provider = params.get("llm_provider", "gemini")

        if not topic and not insights:
            return fail("INSUFFICIENT_EVIDENCE", "No topic or insights", start)

        evidence = _build_evidence(insights, signals)
        if not evidence:
            return fail("INSUFFICIENT_EVIDENCE", "No evidence for brief", start)

        # Budget check — fallback to free Gemini if blocked
        if provider != "gemini" and not _budget_ok(trace_id, provider, len(evidence)):
            provider = "gemini"

        if dry_run:
            return ok({"brief_markdown": "[DRY RUN]", "citations": [], "used_insights": [i.get("id","") for i in insights[:10]], "style_profile": style}, start)

        prompt = _prompt(topic, evidence, params.get("audience","exec"), style, max_len, lang)
        result = _call(provider, params.get("llm_model"), prompt)

        if not result["ok"]:
            return fail(result.get("code", "LLM_REQUEST_FAILED"), result.get("msg", ""), start, retryable=True)

        _track_cost(trace_id, provider, result.get("cost", 0), result.get("tin", 0), result.get("tout", 0))

        return ok({"brief_markdown": result["text"],
                    "citations": [{"id": str(i+1), "source": x.get("source",""), "title": x.get("title","")} for i, x in enumerate(insights[:15])],
                    "used_insights": [x.get("id","") for x in insights[:10]],
                    "style_profile": style}, start, cost_estimate=result.get("cost", 0))
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _build_evidence(insights, signals):
    parts = [f"[{i+1}] {x.get('title','')} (fonte: {x.get('source','?')}, score: {x.get('score',0)})" for i, x in enumerate(insights[:15])]
    parts += [f"[SIGNAL] {s.get('description', str(s))}" for s in (signals or [])[:5]]
    return "\n".join(parts)

def _prompt(topic, evidence, audience, style, max_len, lang):
    return f"""Você é Sofia, assistente de inteligência estratégica.
Gere brief sobre "{topic}". REGRAS: use APENAS evidências abaixo, cite com [N], máx {max_len} chars, {lang}.
{STYLES.get(style, STYLES['professional'])}

EVIDÊNCIAS:
{evidence}

FORMATO: ## [Título] / [Parágrafos com citações] / ### Fontes"""

def _call(provider, model_override, prompt):
    cfg = LLM.get(provider, LLM["gemini"])
    key = os.getenv(cfg["key"], "")
    model = model_override or cfg["model"]
    if not key: return {"ok": False, "code": "LLM_REQUEST_FAILED", "msg": f"Missing {cfg['key']}"}
    try:
        if provider == "gemini":
            r = requests.post(f"{cfg['url'].format(model=model)}?key={key}",
                              json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":2000}}, timeout=55)
            d = r.json(); u = d.get("usageMetadata", {})
            return {"ok": True, "text": d.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text",""),
                    "cost": 0, "tin": u.get("promptTokenCount",0), "tout": u.get("candidatesTokenCount",0)}
        elif provider == "anthropic":
            r = requests.post(cfg["url"], json={"model":model,"max_tokens":2000,"messages":[{"role":"user","content":prompt}]},
                              headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"}, timeout=55)
            d = r.json(); u = d.get("usage",{}); tin, tout = u.get("input_tokens",0), u.get("output_tokens",0)
            return {"ok": True, "text": "".join(b.get("text","") for b in d.get("content",[])),
                    "cost": (tin+tout)/1000*cfg["cost_1k"], "tin": tin, "tout": tout}
        elif provider == "openai":
            r = requests.post(cfg["url"], json={"model":model,"max_tokens":2000,"messages":[{"role":"user","content":prompt}]},
                              headers={"Authorization":f"Bearer {key}","content-type":"application/json"}, timeout=55)
            d = r.json(); u = d.get("usage",{}); tin, tout = u.get("prompt_tokens",0), u.get("completion_tokens",0)
            return {"ok": True, "text": d.get("choices",[{}])[0].get("message",{}).get("content",""),
                    "cost": (tin+tout)/1000*cfg["cost_1k"], "tin": tin, "tout": tout}
    except Exception as e:
        return {"ok": False, "code": "LLM_REQUEST_FAILED", "msg": str(e)}

def _budget_ok(trace_id, provider, evidence_len):
    try:
        from skills.budget_guard.src import execute as check
        est = 0.005 * (evidence_len / 100) if provider != "gemini" else 0
        return check(trace_id, "system", False, {"scope":"day","scope_id":"global","estimated_cost":est}, {"env":"prod"}).get("ok", False)
    except: return True

def _track_cost(trace_id, provider, cost, tin, tout):
    try:
        from skills.budget_guard.src import record_usage
        record_usage(trace_id, "day", "global", "brief.generate", provider, cost, tin, tout)
    except: pass
