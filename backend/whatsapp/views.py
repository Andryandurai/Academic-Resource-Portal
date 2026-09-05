"""The webhook Meta calls, plus two dev-only helpers for testing without
real WhatsApp credentials.

Meta requires a 200 within a few seconds or it re-delivers the same webhook —
so every message is deduplicated by id (`WaMessageLog`) before it is handled,
and a failure handling one message is caught and logged rather than allowed to
turn into a crash loop or a duplicate reply on retry.
"""

from __future__ import annotations

import json
import logging
import threading

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import WaContact, WaMessageLog
from .services import conversation, meta_client

logger = logging.getLogger(__name__)


@require_GET
def webhook_verify(request):
    """Meta's one-time subscription check when the webhook URL is registered."""
    if (
        request.GET.get("hub.mode") == "subscribe"
        and request.GET.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN
        and settings.WHATSAPP_VERIFY_TOKEN
    ):
        return HttpResponse(request.GET.get("hub.challenge", ""), content_type="text/plain")
    return HttpResponseForbidden("Verification failed.")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    """Single URL for both halves of Meta's webhook contract."""
    if request.method == "GET":
        return webhook_verify(request)

    if not meta_client.verify_signature(request.body, request.headers.get("X-Hub-Signature-256")):
        return HttpResponseForbidden("Invalid signature.")

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponse(status=200)  # Malformed body: ack anyway, nothing to retry usefully.

    # Acknowledge Meta immediately. Meta enforces a short response-time budget
    # on webhook delivery, and handling a message can itself make one or more
    # outbound HTTPS calls back to Meta (a reply, a media upload) — blocking
    # this response on that risks the ack itself arriving too late to count,
    # so the actual work runs in the background instead. Dry run has no such
    # external deadline (nothing but a test or a curl call is waiting), so it
    # stays synchronous — deterministic for the test suite and for anyone
    # driving /dev/simulate/ locally.
    if settings.WHATSAPP_DRY_RUN:
        _process_payload(payload)
    else:
        threading.Thread(target=_process_payload, args=(payload,), daemon=True).start()

    return HttpResponse(status=200)


def _process_payload(payload: dict) -> None:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            _handle_change(change.get("value", {}))


def _handle_change(value: dict) -> None:
    profiles_by_wa_id = {
        c.get("wa_id"): c.get("profile", {}).get("name", "") for c in value.get("contacts", [])
    }
    for message in value.get("messages", []):
        try:
            _handle_one_message(message, profiles_by_wa_id)
        except Exception:  # noqa: BLE001 - one bad message must never break the batch
            logger.exception("Failed to handle WhatsApp message %s", message.get("id"))


def _handle_one_message(message: dict, profiles_by_wa_id: dict) -> None:
    message_id = message.get("id")
    from_number = message.get("from")
    if not message_id or not from_number:
        return

    if WaMessageLog.objects.filter(message_id=message_id).exists():
        return  # Redelivery of something we already processed.

    contact, created = WaContact.objects.get_or_create(
        phone_number=from_number,
        defaults={"display_name": profiles_by_wa_id.get(from_number, "")},
    )
    # Recorded before handling: if the handler itself raises, a Meta retry
    # must not re-run it — better to silently drop one message than to loop.
    WaMessageLog.objects.create(message_id=message_id, contact=contact)

    conversation.handle_message(contact, message, is_new_contact=created)


# --------------------------------------------------------------------------- #
# Dev-only helpers — disabled unless WHATSAPP_DRY_RUN is on, so they never
# ship live. Let the whole conversation be built and demoed with curl before a
# Meta developer account exists.
# --------------------------------------------------------------------------- #


@csrf_exempt
@require_http_methods(["POST"])
def dev_simulate(request):
    if not settings.WHATSAPP_DRY_RUN:
        return HttpResponse(status=404)

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    phone = str(payload.get("phone") or "").strip()
    text = str(payload.get("text") or "").strip()
    if not phone or not text:
        return JsonResponse({"detail": "Both \"phone\" and \"text\" are required."}, status=400)

    contact, created = WaContact.objects.get_or_create(phone_number=phone)
    before = len(meta_client.get_dry_run_outbox())
    conversation.handle_message(
        contact, {"type": "text", "text": {"body": text}}, is_new_contact=created
    )
    replies = meta_client.get_dry_run_outbox()[before:]
    return JsonResponse(
        {
            "contact": {"phone_number": contact.phone_number, "state": contact.state},
            "replies": replies,
        }
    )


@require_GET
def dev_outbox(request):
    if not settings.WHATSAPP_DRY_RUN:
        return HttpResponse(status=404)
    return JsonResponse({"outbox": meta_client.get_dry_run_outbox()})
