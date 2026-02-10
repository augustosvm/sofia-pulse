"""
Sofia Skill Runner v1.2

Assinatura canônica (não mude a ordem):
    run(skill_name, params, trace_id=None, actor="system", dry_run=False, env="prod")

trace_id NUNCA vai dentro de params. O runner monta o envelope.

Uso:
    from lib.skill_runner import run
    result = run("logger.event", {"level":"info","event":"test","skill":"test"})
    result = run("collect.run", {"collector_id":"acled"}, trace_id=trace)
"""
import uuid
from importlib import import_module


def run(skill_name: str, params: dict, *, trace_id: str = None,
        actor: str = "system", dry_run: bool = False, env: str = "prod") -> dict:
    """Executa skill. Kwargs após params são keyword-only (asterisco impede posicional)."""
    trace_id = trace_id or str(uuid.uuid4())
    context = {"env": env, "timezone": "America/Sao_Paulo", "locale": "pt-BR"}

    # Guarda: trace_id nunca dentro de params
    if "trace_id" in params:
        params = {k: v for k, v in params.items() if k != "trace_id"}

    module_path = f"skills.{skill_name.replace('.', '_')}.src"
    try:
        module = import_module(module_path)
    except ImportError as e:
        return {"ok": False, "data": None, "warnings": [],
                "errors": [{"code": "INVALID_INPUT", "message": f"Skill not found: {skill_name} ({e})", "retryable": False}],
                "meta": {"duration_ms": 0, "version": "0.0.0"}}
    return module.execute(trace_id, actor, dry_run, params, context)
