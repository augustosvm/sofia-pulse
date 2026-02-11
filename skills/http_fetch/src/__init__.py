"""Sofia Skill: http.fetch — HTTP client com retry, backoff, rate-limit."""

import time, threading, requests as req
from urllib.parse import urlencode
from lib.helpers import ok, fail

_rates = {}
_lock = threading.Lock()
TRANSIENT = {429, 500, 502, 503, 504}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()
    try:
        url = params["url"]
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        query = params.get("query", {})
        body = params.get("body")
        timeout_s = params.get("timeout_ms", 30000) / 1000
        retry_cfg = params.get("retry", {"max": 3, "backoff_ms": 1000})
        expect_json = params.get("expect_json", True)
        rate_key = params.get("rate_limit_key")
        rate_rpm = params.get("rate_limit_rpm", 60)
        max_retries = retry_cfg.get("max", 3)
        backoff_ms = retry_cfg.get("backoff_ms", 1000)

        if dry_run:
            return ok({"status": 0, "dry_run": True, "url": url}, start)

        if rate_key:
            _wait(rate_key, rate_rpm)
        if query:
            url = url + ("&" if "?" in url else "?") + urlencode(query)

        retries_used = 0
        for attempt in range(max_retries + 1):
            try:
                kw = {"headers": headers, "timeout": timeout_s}
                if body and method in ("POST","PUT","PATCH"):
                    kw["json"] = body if isinstance(body, dict) else None
                    if not isinstance(body, dict): kw["data"] = body

                resp = req.request(method, url, **kw)
                if rate_key: _record(rate_key)

                if resp.status_code in TRANSIENT and attempt < max_retries:
                    retries_used += 1
                    ra = resp.headers.get("Retry-After")
                    time.sleep(int(ra) if ra and ra.isdigit() else (backoff_ms/1000)*(2**attempt))
                    continue

                if resp.status_code in (401, 403):
                    return fail("HTTP_AUTH_FAILED", f"{resp.status_code}", start)

                data = {"status": resp.status_code, "headers": dict(resp.headers),
                        "body": resp.text[:50000], "json": None, "retries_used": retries_used}
                if expect_json and "application/json" in resp.headers.get("content-type", ""):
                    try: data["json"] = resp.json()
                    except: pass

                if resp.status_code >= 400:
                    return fail("HTTP_REQUEST_FAILED", f"{resp.status_code}: {resp.text[:200]}", start, retryable=resp.status_code in TRANSIENT)
                return ok(data, start)

            except req.exceptions.Timeout:
                if attempt < max_retries:
                    retries_used += 1; time.sleep((backoff_ms/1000)*(2**attempt)); continue
                return fail("TIMEOUT", f"Timed out after {params.get('timeout_ms',30000)}ms", start, retryable=True)
            except req.exceptions.ConnectionError as e:
                if attempt < max_retries:
                    retries_used += 1; time.sleep((backoff_ms/1000)*(2**attempt)); continue
                return fail("HTTP_REQUEST_FAILED", f"Connection: {e}", start, retryable=True)

        return fail("HTTP_REQUEST_FAILED", "All retries exhausted", start, retryable=True)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)


def _wait(key, rpm):
    with _lock:
        now = time.time()
        _rates.setdefault(key, [])
        _rates[key] = [t for t in _rates[key] if now - t < 60]
        if len(_rates[key]) >= rpm:
            time.sleep(60 - (now - _rates[key][0]) + 0.1)
            _rates[key] = _rates[key][1:]

def _record(key):
    with _lock:
        _rates.setdefault(key, []).append(time.time())
