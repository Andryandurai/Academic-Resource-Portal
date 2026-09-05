"""Thin wrapper around the Meta WhatsApp Cloud API.

Every send function degrades to a log line when `settings.WHATSAPP_DRY_RUN` is
on (the default whenever `DEBUG` is on and no real credentials are configured)
so the whole conversation can be built and demoed — via
`/api/whatsapp/dev/send/` — before a Meta developer account exists at all.

Documents are never sent as a link. `MEDIA_ROOT` is deliberately not a public
URL (see resources/views.py), so a resource's bytes are uploaded straight to
Meta's Media endpoint over the same authenticated, server-to-server call this
module already makes, and the returned `media_id` is what the outgoing message
references — Meta fetches nothing from us over the open internet.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from collections import deque

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 15

#: Meta's own limits — exceeding either is a 400 from the API, not a soft
#: truncation, so callers must respect them before a request is ever sent.
MAX_LIST_ROWS = 10
MAX_BUTTONS = 3

# Dry-run only: the last N outgoing messages, for the local demo endpoint.
# Process-local and unbounded across restarts by design — this is a
# development aid, never a delivery log for a real deployment.
_dry_run_outbox: deque[dict] = deque(maxlen=200)


def get_dry_run_outbox() -> list[dict]:
    return list(_dry_run_outbox)


class MetaConfigError(ImproperlyConfigured):
    """Raised when a real (non-dry-run) call is attempted without credentials."""


def _require_credentials() -> None:
    if not (settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID):
        raise MetaConfigError(
            "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set to send for "
            "real. Set WHATSAPP_DRY_RUN=1 to develop without them."
        )


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Check `X-Hub-Signature-256` so a forged POST cannot impersonate Meta.

    Skipped (returns True) only when no app secret is configured yet, which is
    the state of a fresh dry-run setup — real deployments must set
    WHATSAPP_APP_SECRET, and the webhook view refuses to run without it once
    dry-run is off.

    `WHATSAPP_INSECURE_SKIP_SIGNATURE` is a separate, explicit opt-out for a
    real (non-dry-run) local test session that cannot yet retrieve its App
    secret — e.g. Meta's password-reveal checkpoint failing. Defaults off, so
    an ordinary deployment's security is unaffected by this escape hatch
    existing; never set it outside a throwaway local `.env`.
    """
    if settings.WHATSAPP_INSECURE_SKIP_SIGNATURE:
        return True
    if not settings.WHATSAPP_APP_SECRET:
        return settings.WHATSAPP_DRY_RUN
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix("sha256="))


def _post(path: str, **kwargs) -> dict:
    _require_credentials()
    url = f"{settings.WHATSAPP_GRAPH_BASE}/{path}"
    headers = kwargs.pop("headers", {})
    headers.setdefault("Authorization", f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}")
    response = requests.post(url, headers=headers, timeout=_REQUEST_TIMEOUT_SECONDS, **kwargs)
    if not response.ok:
        logger.error("Meta API error %s: %s", response.status_code, response.text[:500])
    response.raise_for_status()
    return response.json()


def _send_message(to: str, payload: dict) -> None:
    body = {"messaging_product": "whatsapp", "to": to, **payload}
    if settings.WHATSAPP_DRY_RUN:
        _dry_run_outbox.append({"to": to, **payload})
        logger.info("[WHATSAPP DRY RUN] -> %s: %s", to, payload)
        return
    _post(f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages", json=body)


def send_text(to: str, body: str) -> None:
    _send_message(to, {"type": "text", "text": {"body": body[:4096]}})


def send_interactive_buttons(to: str, body: str, buttons: list[tuple[str, str]]) -> None:
    """`buttons` is `[(id, title), ...]`, at most 3, each title at most 20 chars."""
    buttons = buttons[:MAX_BUTTONS]
    _send_message(
        to,
        {
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body[:1024]},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": bid, "title": title[:20]}}
                        for bid, title in buttons
                    ]
                },
            },
        },
    )


def send_interactive_list(to: str, body: str, button_text: str, sections: list[dict]) -> None:
    """`sections` is `[{"title": str, "rows": [{"id", "title", "description"?}]}]`.

    Rows are truncated to fit Meta's per-row limits (24/72 chars) rather than
    rejected, and the row count is hard-capped at 10 total across every
    section — callers with more than 10 candidates must page or narrow first.
    """
    trimmed = []
    rows_used = 0
    for section in sections:
        if rows_used >= MAX_LIST_ROWS:
            break
        rows = []
        for row in section["rows"]:
            if rows_used >= MAX_LIST_ROWS:
                break
            rows.append(
                {
                    "id": row["id"],
                    "title": row["title"][:24],
                    **({"description": row["description"][:72]} if row.get("description") else {}),
                }
            )
            rows_used += 1
        if rows:
            trimmed.append({"title": section["title"][:24], "rows": rows})

    _send_message(
        to,
        {
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body[:1024]},
                "action": {"button": button_text[:20], "sections": trimmed},
            },
        },
    )


def upload_media(file_obj, filename: str, mime_type: str) -> str:
    """Upload bytes to Meta and return the `media_id` to reference in a send.

    Dry run returns a synthetic id so the conversation flow can be exercised
    end-to-end without real credentials.
    """
    if settings.WHATSAPP_DRY_RUN:
        fake_id = f"dry-run-media:{filename}"
        logger.info("[WHATSAPP DRY RUN] uploaded %s (%s) -> %s", filename, mime_type, fake_id)
        return fake_id

    data = _post(
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/media",
        data={"messaging_product": "whatsapp"},
        files={"file": (filename, file_obj, mime_type)},
    )
    return data["id"]


def send_document(to: str, media_id: str, filename: str, caption: str = "") -> None:
    payload = {"type": "document", "document": {"id": media_id, "filename": filename}}
    if caption:
        payload["document"]["caption"] = caption[:1024]
    _send_message(to, payload)
