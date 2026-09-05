"""End-to-end conversation flow, verified through the dry-run outbox.

`meta_client.WHATSAPP_DRY_RUN` (forced on by the autouse fixture in
conftest.py) means every "send" is just appended to an in-process list instead
of calling Meta — these tests read that list the way an integration test would
read a captured HTTP request.
"""

from __future__ import annotations

import pytest

from conftest import pdf_upload
from resources.models import ContentKind, Resource, ResourceType

from whatsapp.models import ConversationState, WaContact
from whatsapp.services import conversation, meta_client

pytestmark = pytest.mark.django_db


def outbox():
    return meta_client.get_dry_run_outbox()


def last():
    box = outbox()
    assert box, "expected at least one outgoing message"
    return box[-1]


def text_message(phone: str, body: str, **kwargs):
    conversation.handle_message(
        _contact(phone), {"type": "text", "text": {"body": body}}, **kwargs
    )


def _contact(phone: str) -> WaContact:
    contact, _ = WaContact.objects.get_or_create(phone_number=phone)
    return contact


def interactive_reply(contact: WaContact, reply_id: str) -> None:
    conversation.handle_message(
        contact,
        {"type": "interactive", "interactive": {"list_reply": {"id": reply_id}}},
        is_new_contact=False,
    )


# --------------------------------------------------------------------------- #
# Onboarding
# --------------------------------------------------------------------------- #


def test_new_contact_gets_welcome_and_department_prompt():
    contact = WaContact.objects.create(phone_number="910000000001")
    conversation.handle_message(
        contact, {"type": "text", "text": {"body": "hi, anything works here"}}, is_new_contact=True
    )
    assert contact.state == ConversationState.AWAITING_DEPARTMENT
    assert len(outbox()) == 2
    assert "Welcome" in outbox()[0]["text"]["body"]
    assert "department" in outbox()[1]["text"]["body"].lower()


def test_department_then_semester_selection(curriculum, data_structures):
    contact = WaContact.objects.create(phone_number="910000000002")

    conversation.handle_message(
        contact, {"type": "text", "text": {"body": "AI&DS"}}, is_new_contact=False
    )
    contact.refresh_from_db()
    assert contact.department_id == curriculum.pk
    assert contact.state == ConversationState.AWAITING_SEMESTER
    assert last()["interactive"]["type"] == "list"

    interactive_reply(contact, f"sem:{data_structures.semester_id}")
    contact.refresh_from_db()
    assert contact.semester_id == data_structures.semester_id
    assert contact.state == ConversationState.IDLE


def test_unmatched_department_asks_again():
    contact = WaContact.objects.create(phone_number="910000000003")
    conversation.handle_message(
        contact, {"type": "text", "text": {"body": "xyzxyz not a department"}}, is_new_contact=False
    )
    assert contact.state == ConversationState.AWAITING_DEPARTMENT
    assert "couldn't match" in last()["text"]["body"]


# --------------------------------------------------------------------------- #
# Direct form: "unit 1 data structure notes" needs no menu round trip.
# --------------------------------------------------------------------------- #


def test_direct_query_delivers_notes_document(ready_contact, data_structures):
    resource = Resource.objects.create(
        subject=data_structures,
        resource_type=ResourceType.UNIT_1,
        kind=ContentKind.NOTES,
        title="Unit 1 Notes",
        file=pdf_upload("unit1.pdf"),
        file_name="unit1.pdf",
        file_type="application/pdf",
        file_ext="pdf",
    )

    conversation.handle_message(
        ready_contact,
        {"type": "text", "text": {"body": "unit 1 data structure notes"}},
        is_new_contact=False,
    )

    documents = [m for m in outbox() if m.get("type") == "document"]
    assert len(documents) == 1
    assert documents[0]["document"]["filename"] == "unit1.pdf"
    ready_contact.refresh_from_db()
    assert ready_contact.state == ConversationState.IDLE
    assert ready_contact.context == {}


def test_direct_query_delivers_reference_link(ready_contact, data_structures):
    Resource.objects.create(
        subject=data_structures,
        resource_type=ResourceType.UNIT_2,
        kind=ContentKind.REFERENCE,
        title="GeeksForGeeks — Linked Lists",
        url="https://example.com/linked-lists",
    )

    conversation.handle_message(
        ready_contact,
        {"type": "text", "text": {"body": "unit 2 data structures reference links"}},
        is_new_contact=False,
    )

    assert "https://example.com/linked-lists" in outbox()[-2]["text"]["body"]


def test_missing_resource_says_so_without_crashing(ready_contact, data_structures):
    conversation.handle_message(
        ready_contact,
        {"type": "text", "text": {"body": "unit 5 data structure youtube videos"}},
        is_new_contact=False,
    )
    assert "nothing has been published" in last()["text"]["body"].lower()


# --------------------------------------------------------------------------- #
# Menu round trip: subject named, then unit and kind asked one at a time.
# --------------------------------------------------------------------------- #


def test_menu_round_trip_by_button_taps(ready_contact, data_structures):
    resource = Resource.objects.create(
        subject=data_structures,
        resource_type=ResourceType.UNIT_3,
        kind=ContentKind.YOUTUBE,
        title="Trees explained",
        url="https://youtu.be/abc123",
    )

    conversation.handle_message(
        ready_contact, {"type": "text", "text": {"body": "data structures"}}, is_new_contact=False
    )
    assert last()["interactive"]["type"] == "list"  # unit menu
    context = ready_contact.context
    assert context["subject_id"] == data_structures.pk

    interactive_reply(ready_contact, f"unit:{ResourceType.UNIT_3}")
    assert last()["interactive"]["type"] == "button"  # kind menu

    interactive_reply(ready_contact, f"kind:{ContentKind.YOUTUBE}")
    assert resource.url in outbox()[-2]["text"]["body"]
    ready_contact.refresh_from_db()
    assert ready_contact.state == ConversationState.IDLE
    assert ready_contact.context == {}


def test_menu_round_trip_by_typed_answers(ready_contact, data_structures):
    Resource.objects.create(
        subject=data_structures,
        resource_type=ResourceType.CAT_1,
        kind=ContentKind.NOTES,
        title="CAT 1 model paper",
        file=pdf_upload("cat1.pdf"),
        file_name="cat1.pdf",
        file_type="application/pdf",
        file_ext="pdf",
    )

    text_message(ready_contact.phone_number, "data structures", is_new_contact=False)
    ready_contact.refresh_from_db()
    text_message(ready_contact.phone_number, "cat 1", is_new_contact=False)
    ready_contact.refresh_from_db()
    text_message(ready_contact.phone_number, "notes", is_new_contact=False)

    documents = [m for m in outbox() if m.get("type") == "document"]
    assert len(documents) == 1


# --------------------------------------------------------------------------- #
# Ambiguous subject -> "did you mean" -> numeric pick
# --------------------------------------------------------------------------- #


def test_ambiguous_subject_offers_shortlist_then_resolves(ambiguous_semester):
    semester, maths_1, maths_2 = ambiguous_semester
    contact = WaContact.objects.create(
        phone_number="910000000004",
        department=semester.department,
        semester=semester,
        state=ConversationState.IDLE,
    )

    conversation.handle_message(
        contact, {"type": "text", "text": {"body": "engineering mathematics"}}, is_new_contact=False
    )
    contact.refresh_from_db()
    assert contact.state == ConversationState.AWAITING_SUBJECT_CHOICE
    rows = last()["interactive"]["action"]["sections"][0]["rows"]
    assert {r["id"] for r in rows} >= {f"subj:{maths_1.pk}", f"subj:{maths_2.pk}"}

    conversation.handle_message(
        contact, {"type": "text", "text": {"body": "1"}}, is_new_contact=False
    )
    contact.refresh_from_db()
    # Picking a candidate with no unit/kind pending asks the unit menu next.
    assert contact.state == ConversationState.IDLE
    assert contact.context["subject_id"] in {maths_1.pk, maths_2.pk}
    assert last()["interactive"]["type"] == "list"


# --------------------------------------------------------------------------- #
# Global commands
# --------------------------------------------------------------------------- #


def test_restart_command_clears_everything(ready_contact):
    conversation.handle_message(
        ready_contact, {"type": "text", "text": {"body": "restart"}}, is_new_contact=False
    )
    ready_contact.refresh_from_db()
    assert ready_contact.department is None
    assert ready_contact.semester is None
    assert ready_contact.state == ConversationState.AWAITING_DEPARTMENT


def test_menu_command_shows_status(ready_contact):
    conversation.handle_message(
        ready_contact, {"type": "text", "text": {"body": "menu"}}, is_new_contact=False
    )
    assert ready_contact.department.name in last()["text"]["body"]
