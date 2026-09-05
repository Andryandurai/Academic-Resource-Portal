"""The webhook Meta calls: verification handshake, signature check, and
idempotent message handling.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from django.urls import reverse

from whatsapp.models import WaContact, WaMessageLog
from whatsapp.services import meta_client

pytestmark = pytest.mark.django_db

WEBHOOK_URL = "/api/whatsapp/webhook/"
SIMULATE_URL = "/api/whatsapp/dev/simulate/"
OUTBOX_URL = "/api/whatsapp/dev/outbox/"


def test_webhook_url_names_resolve():
    assert reverse("whatsapp-webhook") == WEBHOOK_URL
    assert reverse("whatsapp-dev-simulate") == SIMULATE_URL
    assert reverse("whatsapp-dev-outbox") == OUTBOX_URL


def test_verify_challenge_success(client, settings):
    settings.WHATSAPP_VERIFY_TOKEN = "the-secret-token"
    response = client.get(
        WEBHOOK_URL,
        {"hub.mode": "subscribe", "hub.verify_token": "the-secret-token", "hub.challenge": "12345"},
    )
    assert response.status_code == 200
    assert response.content == b"12345"


def test_verify_challenge_wrong_token(client, settings):
    settings.WHATSAPP_VERIFY_TOKEN = "the-secret-token"
    response = client.get(
        WEBHOOK_URL,
        {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "12345"},
    )
    assert response.status_code == 403


def _message_payload(message_id: str, phone: str, body: str) -> bytes:
    return json.dumps(
        {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "contacts": [{"wa_id": phone, "profile": {"name": "Test User"}}],
                                "messages": [
                                    {
                                        "from": phone,
                                        "id": message_id,
                                        "type": "text",
                                        "text": {"body": body},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
    ).encode("utf-8")


def _signed(client, url, raw_body: bytes, secret: str):
    signature = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return client.post(url, data=raw_body, content_type="application/json", HTTP_X_HUB_SIGNATURE_256=signature)


def test_post_without_secret_configured_is_accepted(client, settings):
    """Dry-run + no app secret is the fresh-setup state: signing is not required yet."""
    settings.WHATSAPP_APP_SECRET = ""
    settings.WHATSAPP_DRY_RUN = True
    body = _message_payload("wamid.1", "910000000010", "hi")

    response = client.post(WEBHOOK_URL, data=body, content_type="application/json")

    assert response.status_code == 200
    assert WaContact.objects.filter(phone_number="910000000010").exists()
    assert WaMessageLog.objects.filter(message_id="wamid.1").exists()
    assert meta_client.get_dry_run_outbox()  # onboarding reply was sent


def test_post_with_wrong_signature_rejected(client, settings):
    settings.WHATSAPP_APP_SECRET = "shh-its-a-secret"
    body = _message_payload("wamid.2", "910000000011", "hi")

    response = client.post(
        WEBHOOK_URL, data=body, content_type="application/json", HTTP_X_HUB_SIGNATURE_256="sha256=deadbeef"
    )

    assert response.status_code == 403
    assert not WaContact.objects.filter(phone_number="910000000011").exists()


def test_post_with_correct_signature_accepted(client, settings):
    settings.WHATSAPP_APP_SECRET = "shh-its-a-secret"
    body = _message_payload("wamid.3", "910000000012", "hi")

    response = _signed(client, WEBHOOK_URL, body, "shh-its-a-secret")

    assert response.status_code == 200
    assert WaContact.objects.filter(phone_number="910000000012").exists()


def test_duplicate_message_id_is_processed_once(client, settings):
    settings.WHATSAPP_APP_SECRET = ""
    body = _message_payload("wamid.4", "910000000013", "hi")

    client.post(WEBHOOK_URL, data=body, content_type="application/json")
    first_count = len(meta_client.get_dry_run_outbox())
    client.post(WEBHOOK_URL, data=body, content_type="application/json")
    second_count = len(meta_client.get_dry_run_outbox())

    assert WaMessageLog.objects.filter(message_id="wamid.4").count() == 1
    assert second_count == first_count  # the redelivery produced no new reply


def test_malformed_json_body_is_acked_not_retried(client, settings):
    settings.WHATSAPP_APP_SECRET = ""
    response = client.post(WEBHOOK_URL, data=b"not json", content_type="application/json")
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# Dev-only helpers
# --------------------------------------------------------------------------- #


def test_dev_simulate_and_outbox(client, settings):
    settings.WHATSAPP_DRY_RUN = True
    response = client.post(
        SIMULATE_URL,
        data=json.dumps({"phone": "910000000099", "text": "hello there"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["contact"]["phone_number"] == "910000000099"
    assert data["replies"]

    outbox_response = client.get(OUTBOX_URL)
    assert outbox_response.status_code == 200
    assert outbox_response.json()["outbox"]


def test_dev_endpoints_disabled_outside_dry_run(client, settings):
    settings.WHATSAPP_DRY_RUN = False
    assert client.post(
        SIMULATE_URL, data=json.dumps({"phone": "1", "text": "hi"}), content_type="application/json"
    ).status_code == 404
    assert client.get(OUTBOX_URL).status_code == 404


def test_dev_simulate_requires_phone_and_text(client, settings):
    settings.WHATSAPP_DRY_RUN = True
    response = client.post(SIMULATE_URL, data=json.dumps({}), content_type="application/json")
    assert response.status_code == 400
