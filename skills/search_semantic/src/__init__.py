"""Sofia Skill: search.semantic — RAG sobre pgvector. Sem alucinação: vazio se não achar."""

import os, time, json, requests, psycopg2
from lib.helpers import ok, fail, DB_URL

EMB = {
    "gemini": {"url": "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent",
               "key": "GEMINI_API_KEY", "dim": 768, "cost": 0.0},
    "openai": {"url": "https://api.openai.com/v1/embeddings",
               "key": "OPENAI_API_KEY", "dim": 1536, "cost": 0.00002},
}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        query = params.get("query", "")
        if not query: return fail("INVALID_INPUT", "Query empty", start)
        top_k = params.get("top_k", 5)
        filters = params.get("filters", {})
        provider = params.get("embedding_provider", "gemini")
        threshold = params.get("similarity_threshold", 0.7)

        if dry_run:
            return ok({"hits": [], "query": query, "total_searched": 0}, start)

        embedding = _embed(query, provider)
        if not embedding:
            return fail("SEARCH_EMBEDDING_FAILED", f"Failed with {provider}", start, retryable=True)

        hits = _search(embedding, top_k, filters, threshold)
        cost = EMB.get(provider, {}).get("cost", 0)

        if not hits:
            return ok({"hits": [], "query": query, "total_searched": 0}, start, cost_estimate=cost,
                      warnings=[{"code": "SEARCH_NO_RESULTS", "message": "No matches"}])
        return ok({"hits": hits, "query": query, "total_searched": len(hits)}, start, cost_estimate=cost)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _embed(text, provider):
    cfg = EMB.get(provider, EMB["gemini"])
    key = os.getenv(cfg["key"], "")
    if not key: return None
    try:
        if provider == "gemini":
            r = requests.post(f"{cfg['url']}?key={key}",
                              json={"model":"models/text-embedding-004","content":{"parts":[{"text":text}]}}, timeout=15)
            return r.json().get("embedding", {}).get("values")
        elif provider == "openai":
            r = requests.post(cfg["url"], json={"input": text, "model": "text-embedding-3-small"},
                              headers={"Authorization": f"Bearer {key}"}, timeout=15)
            return r.json().get("data", [{}])[0].get("embedding")
    except: return None


def _search(embedding, top_k, filters, threshold):
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        wheres, pvals = [], []
        for col, key in [("entity_type","entity_type"),("source","source")]:
            if filters.get(key): wheres.append(f"{col}=%s"); pvals.append(filters[key])
        if filters.get("since"): wheres.append("created_at>=%s"); pvals.append(filters["since"])
        if filters.get("until"): wheres.append("created_at<=%s"); pvals.append(filters["until"])
        if filters.get("country"): wheres.append("metadata->>'country'=%s"); pvals.append(filters["country"])

        where_sql = " AND ".join(wheres) if wheres else "TRUE"
        emb_str = "[" + ",".join(str(x) for x in embedding) + "]"

        cur.execute(f"""SELECT id, entity_type, source, title, content, url, metadata,
                        1-(embedding <=> %s::vector) AS sim
                    FROM sofia.embeddings WHERE {where_sql}
                    ORDER BY embedding <=> %s::vector LIMIT %s""",
                    [emb_str] + pvals + [emb_str, top_k])

        hits = []
        for r in cur.fetchall():
            sim = float(r[7])
            if sim < threshold: continue
            hits.append({"id": str(r[0]), "entity_type": r[1], "source": r[2], "title": r[3] or "",
                         "snippet": (r[4] or "")[:500], "url": r[5] or "", "score": round(sim, 4),
                         "metadata": r[6] or {}})
        cur.close(); conn.close()
        return hits
    except: return []


def ingest(trace_id, entity_type, source, source_id, title, content, url="", metadata=None, provider="gemini"):
    """Insere documento com embedding."""
    embedding = _embed(content[:5000], provider)
    if not embedding: return False
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        emb_str = "[" + ",".join(str(x) for x in embedding) + "]"
        cur.execute("""INSERT INTO sofia.embeddings (entity_type,source,source_id,title,content,embedding,url,metadata)
                    VALUES (%s,%s,%s,%s,%s,%s::vector,%s,%s::jsonb) ON CONFLICT (id) DO NOTHING""",
                    (entity_type, source, source_id, title, content[:10000], emb_str, url, json.dumps(metadata or {})))
        conn.commit(); cur.close(); conn.close(); return True
    except: return False
