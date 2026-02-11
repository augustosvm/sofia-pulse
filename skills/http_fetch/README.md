# http.fetch
HTTP client com retry exponencial, rate-limit por chave, timeout.
Retries APENAS em 429/5xx. Substitui requests.get() puro nos collectors Python.
