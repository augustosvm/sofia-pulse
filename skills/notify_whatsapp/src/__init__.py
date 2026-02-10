"""Sofia Skill: notify.whatsapp — Envia notificações via WhatsApp (Baileys).

Encapsula chamada para WhatsApp API (Baileys) rodando em WHATSAPP_API_URL.
NÃO fala direto com Baileys, usa API HTTP intermediária.
"""

import os
import time
import requests
from lib.helpers import ok, fail


# Mapeamento de severity para emoji
SEVERITY_EMOJI = {
    "info": "ℹ️",
    "warning": "⚠️",
    "critical": "🚨",
}


def execute(trace_id, actor, dry_run, params, context):
    start = time.time()

    # Validação básica
    if "title" not in params or "message" not in params:
        return fail("INVALID_INPUT", "title and message are required", start)

    # Resolver destinatário
    to = params.get("to", "admin")
    if to == "admin":
        # Usar número admin do env
        admin_number = os.getenv("WHATSAPP_ADMIN_NUMBER", os.getenv("WHATSAPP_NUMBER", "5527988024062"))
        to_number = admin_number
    else:
        # Usar número fornecido diretamente
        to_number = to

    # Construir mensagem formatada
    severity = params.get("severity", "info")
    emoji = SEVERITY_EMOJI.get(severity, "📢")
    title = params["title"]
    message_body = params["message"]
    summary = params.get("summary")

    # Formato WhatsApp (markdown simples)
    full_message = f"{emoji} *{title}*\n\n{message_body}"

    # Se há summary, adicionar ao final
    if summary and isinstance(summary, dict):
        full_message += "\n\n*Summary:*"
        for key, value in summary.items():
            full_message += f"\n• {key}: {value}"

    # Dry run
    if dry_run:
        return ok({
            "sent": False,
            "to": to_number,
            "message_preview": full_message[:100],
            "dry_run": True
        }, start)

    # Chamar API WhatsApp
    api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:3001/send")
    enabled = os.getenv("WHATSAPP_ENABLED", "true").lower() == "true"

    if not enabled:
        # WhatsApp desabilitado, apenas log
        return ok({
            "sent": False,
            "to": to_number,
            "message_preview": full_message[:100],
            "disabled": True
        }, start, warnings=[{"code": "WHATSAPP_DISABLED", "message": "WHATSAPP_ENABLED=false"}])

    try:
        response = requests.post(
            api_url,
            json={"to": to_number, "message": full_message},
            timeout=10
        )

        if response.status_code == 200:
            return ok({
                "sent": True,
                "to": to_number,
                "api_status": response.status_code,
                "message_preview": full_message[:100]
            }, start)
        else:
            return fail(
                "HTTP_REQUEST_FAILED",
                f"WhatsApp API returned {response.status_code}: {response.text[:200]}",
                start,
                retryable=True
            )

    except requests.Timeout:
        return fail("TIMEOUT", "WhatsApp API timeout", start, retryable=True)
    except requests.ConnectionError:
        return fail("HTTP_REQUEST_FAILED", "Cannot connect to WhatsApp API", start, retryable=True)
    except Exception as e:
        return fail("UNKNOWN_ERROR", str(e), start)
