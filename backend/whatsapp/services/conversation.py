"""The state machine: one incoming WhatsApp message in, zero or more sent.

Deliberately not a rigid step-1-then-step-2-then-step-3 wizard. Every free-text
message is re-parsed from scratch (`nlp.extract_intent`) and merged onto
whatever the bot already knew about this conversation (`contact.context`), so
a student can answer a menu with a button tap *or* by just typing the answer
("notes"), and can abandon a half-finished menu to ask about a different
subject entirely without getting stuck. See `WaContact.state` in models.py for
why only four states exist.
"""

from __future__ import annotations

import logging
import re

from academics.models import Semester, Subject
from resources.models import ContentKind

from . import catalog, meta_client, nlp
from ..models import ConversationState, WaContact

logger = logging.getLogger(__name__)

_GREETINGS = {"hi", "hello", "hey", "start", "help", "menu"}
_RESTART_COMMANDS = {"restart", "reset", "change department", "switch department", "department"}

_ROMAN_SEMESTERS = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8,
}
_SUBJECT_MARGIN = 0.08  # top score must clear the runner-up by this much to skip the "did you mean"


def handle_message(contact: WaContact, message: dict, *, is_new_contact: bool) -> None:
    if is_new_contact:
        meta_client.send_text(
            contact.phone_number,
            "👋 Welcome to the REC Academic Resource Bot!\n\n"
            "I can send you unit notes, reference links and YouTube videos for "
            "any subject — just ask, e.g. \"unit 1 data structures notes\".\n\n"
            "First, let's set up your department and semester.",
        )
        _ask_department(contact)
        return

    msg_type = message.get("type")
    if msg_type == "interactive":
        interactive = message.get("interactive", {})
        reply = interactive.get("list_reply") or interactive.get("button_reply")
        _handle_reply_id(contact, reply.get("id") if reply else None)
        return
    if msg_type == "button":
        _handle_reply_id(contact, message.get("button", {}).get("payload"))
        return
    if msg_type == "text":
        _handle_text(contact, message.get("text", {}).get("body", ""))
        return

    meta_client.send_text(
        contact.phone_number,
        "I can only understand text messages right now — please type what you need.",
    )


# --------------------------------------------------------------------------- #
# Free text
# --------------------------------------------------------------------------- #


def _handle_text(contact: WaContact, raw_text: str) -> None:
    text = (raw_text or "").strip()
    low = _normalize(text)
    if not text:
        return

    if low in _GREETINGS:
        _send_status_or_help(contact)
        return
    if low in _RESTART_COMMANDS:
        contact.department = None
        contact.semester = None
        contact.context = {}
        contact.state = ConversationState.AWAITING_DEPARTMENT
        contact.save()
        _ask_department(contact)
        return

    if contact.state == ConversationState.AWAITING_DEPARTMENT:
        _handle_department_text(contact, text)
        return
    if contact.state == ConversationState.AWAITING_SEMESTER:
        _handle_semester_text(contact, text)
        return
    if contact.state == ConversationState.AWAITING_SUBJECT_CHOICE:
        picked = _resolve_shortlist_pick(contact, low)
        if picked is not None:
            pending = {k: v for k, v in contact.context.items() if k != "candidates"}
            _advance(contact, {"subject_id": picked.id, **pending})
            return
        # Didn't look like "pick #2" — the student has moved on to a new
        # question, so drop the stale shortlist and fall through below.
        contact.context = {}

    if contact.department is None or contact.semester is None:
        # Defensive only: IDLE/AWAITING_SUBJECT_CHOICE should never be reached
        # without both set.
        contact.state = ConversationState.AWAITING_DEPARTMENT
        contact.save()
        _ask_department(contact)
        return

    _handle_query_text(contact, text)


def _handle_department_text(contact: WaContact, text: str) -> None:
    dept = catalog.find_department(text)
    if dept is None:
        meta_client.send_text(
            contact.phone_number,
            "I couldn't match that to a department. Please reply with your department's "
            "name or short code — e.g. \"CSE\" or \"Computer Science and Engineering\".",
        )
        return
    contact.department = dept
    contact.semester = None
    contact.context = {}
    contact.state = ConversationState.AWAITING_SEMESTER
    contact.save()
    _ask_semester(contact)


def _handle_semester_text(contact: WaContact, text: str) -> None:
    semester = _resolve_semester_text(contact.department, text)
    if semester is None:
        meta_client.send_text(
            contact.phone_number,
            "Please reply with your semester — e.g. \"3\" or \"Semester III\".",
        )
        return
    contact.semester = semester
    contact.reset_to_idle()
    contact.save()
    meta_client.send_text(
        contact.phone_number,
        f"You're set up for {contact.department.name}, {semester.name}. ✅\n\n"
        "Ask me about any subject — e.g. \"unit 1 data structures notes\", or just "
        "\"data structures\" and I'll ask what you need.\n\n"
        "Type \"menu\" anytime for this help, or \"change department\" to switch.",
    )


def _handle_query_text(contact: WaContact, text: str) -> None:
    intent = nlp.extract_intent(text)

    if intent.subject_query:
        matches = catalog.resolve_subjects(contact.semester, intent.subject_query)
        if not matches:
            contact.reset_to_idle()
            contact.save()
            meta_client.send_text(
                contact.phone_number,
                f"I couldn't find a subject matching \"{intent.subject_query}\" in "
                f"{contact.semester.name}. Please check the name and try again.",
            )
            return

        pending = {}
        if intent.unit:
            pending["resource_type"] = intent.unit
        if intent.kind:
            pending["kind"] = intent.kind

        top = matches[0]
        clearly_best = len(matches) == 1 or (top.score - matches[1].score) >= _SUBJECT_MARGIN
        if clearly_best and top.score >= catalog.CONFIDENT_SUBJECT_SCORE:
            _advance(contact, {"subject_id": top.subject.id, **pending})
        else:
            _ask_subject_choice(contact, matches, pending)
        return

    # No subject named this turn — this can only be answering a pending
    # unit/kind question from earlier in the conversation.
    known = dict(contact.context)
    if intent.unit:
        known["resource_type"] = intent.unit
    if intent.kind:
        known["kind"] = intent.kind

    if "subject_id" not in known:
        contact.reset_to_idle()
        contact.save()
        meta_client.send_text(
            contact.phone_number,
            "Which subject is that for? Tell me its name, e.g. \"Data Structures\".",
        )
        return

    _advance(contact, known)


# --------------------------------------------------------------------------- #
# Interactive (button / list) replies
# --------------------------------------------------------------------------- #


def _handle_reply_id(contact: WaContact, reply_id: str | None) -> None:
    if not reply_id or ":" not in reply_id:
        meta_client.send_text(
            contact.phone_number, "Sorry, I didn't catch that. Type \"menu\" to start over."
        )
        return

    prefix, _, value = reply_id.partition(":")

    if prefix == "sem":
        semester = Semester.objects.filter(pk=value, department=contact.department).first()
        if semester is None:
            meta_client.send_text(contact.phone_number, "That option expired — please try again.")
            return
        contact.semester = semester
        contact.reset_to_idle()
        contact.save()
        meta_client.send_text(
            contact.phone_number,
            f"You're set up for {contact.department.name}, {semester.name}. ✅\n\n"
            "Ask me about any subject — e.g. \"unit 1 data structures notes\".",
        )
        return

    if prefix == "subj":
        if contact.semester is None:
            _ask_department(contact)
            return
        subject = Subject.objects.filter(pk=value, semester=contact.semester).first()
        if subject is None:
            contact.reset_to_idle()
            contact.save()
            meta_client.send_text(contact.phone_number, "That option expired — please ask again.")
            return
        pending = {k: v for k, v in contact.context.items() if k != "candidates"}
        _advance(contact, {"subject_id": subject.id, **pending})
        return

    if prefix == "unit":
        known = dict(contact.context)
        known["resource_type"] = value
        if "subject_id" not in known:
            contact.reset_to_idle()
            contact.save()
            meta_client.send_text(
                contact.phone_number, "That session expired — please tell me the subject again."
            )
            return
        _advance(contact, known)
        return

    if prefix == "kind":
        known = dict(contact.context)
        known["kind"] = value
        if "subject_id" not in known or "resource_type" not in known:
            contact.reset_to_idle()
            contact.save()
            meta_client.send_text(
                contact.phone_number, "That session expired — please ask again from the start."
            )
            return
        _advance(contact, known)
        return

    meta_client.send_text(
        contact.phone_number, "Sorry, I didn't catch that. Type \"menu\" to start over."
    )


# --------------------------------------------------------------------------- #
# Shared "what do we still need to know" step
# --------------------------------------------------------------------------- #


def _advance(contact: WaContact, known: dict) -> None:
    """Given whatever the conversation has learned so far, ask the next
    question or, once subject + unit + kind are all known, deliver.
    """
    subject = Subject.objects.select_related("semester", "semester__department").filter(
        pk=known.get("subject_id")
    ).first()
    if subject is None or subject.semester_id != contact.semester_id:
        contact.reset_to_idle()
        contact.save()
        meta_client.send_text(
            contact.phone_number, "That subject is no longer available — please ask again."
        )
        return

    resource_type = known.get("resource_type")
    kind = known.get("kind")

    if not resource_type:
        contact.state = ConversationState.IDLE
        contact.context = {"subject_id": subject.id, **({"kind": kind} if kind else {})}
        contact.save()
        _ask_unit(contact, subject)
        return

    if not catalog.has_any_resource(subject, resource_type):
        contact.reset_to_idle()
        contact.save()
        label = catalog.RESOURCE_TYPE_LABELS.get(resource_type, resource_type)
        meta_client.send_text(
            contact.phone_number,
            f"Nothing has been published yet for {subject.course_title} — {label}. "
            "Try a different unit, or ask again later.",
        )
        return

    if not kind:
        contact.state = ConversationState.IDLE
        contact.context = {"subject_id": subject.id, "resource_type": resource_type}
        contact.save()
        _ask_kind(contact, subject, resource_type)
        return

    contact.reset_to_idle()
    contact.save()
    _deliver(contact, subject, resource_type, kind)


# --------------------------------------------------------------------------- #
# Outgoing prompts
# --------------------------------------------------------------------------- #


def _send_status_or_help(contact: WaContact) -> None:
    if contact.department and contact.semester:
        meta_client.send_text(
            contact.phone_number,
            f"You're set up for {contact.department.name}, {contact.semester.name}.\n\n"
            "Ask me about any subject — e.g. \"unit 1 data structures notes\", or just "
            "\"data structures\" and I'll ask what you need.\n\n"
            "Type \"change department\" to switch.",
        )
        return
    if contact.department:
        _ask_semester(contact)
        return
    _ask_department(contact)


def _ask_department(contact: WaContact) -> None:
    contact.state = ConversationState.AWAITING_DEPARTMENT
    contact.save()
    lines = [f"• {d.code} — {d.name}" for d in catalog.departments_with_curriculum()]
    meta_client.send_text(
        contact.phone_number,
        "Which department are you in? Reply with its name or short code.\n\n" + "\n".join(lines),
    )


def _ask_semester(contact: WaContact) -> None:
    contact.state = ConversationState.AWAITING_SEMESTER
    contact.save()
    semesters = list(catalog.semesters_for(contact.department))
    meta_client.send_interactive_list(
        contact.phone_number,
        f"{contact.department.name} — which semester are you in?",
        "Choose semester",
        [{"title": "Semester", "rows": [{"id": f"sem:{s.id}", "title": s.name} for s in semesters]}],
    )


def _ask_subject_choice(contact: WaContact, matches: list[catalog.SubjectMatch], pending: dict) -> None:
    contact.state = ConversationState.AWAITING_SUBJECT_CHOICE
    contact.context = {"candidates": [m.subject.id for m in matches], **pending}
    contact.save()
    rows = [
        {
            "id": f"subj:{m.subject.id}",
            "title": m.subject.course_title,
            "description": m.subject.course_code or "",
        }
        for m in matches
    ]
    meta_client.send_interactive_list(
        contact.phone_number,
        "Did you mean one of these? You can also reply with the number.",
        "Choose subject",
        [{"title": "Closest matches", "rows": rows}],
    )


def _ask_unit(contact: WaContact, subject: Subject) -> None:
    meta_client.send_interactive_list(
        contact.phone_number,
        f"{subject.course_title} — what do you need?",
        "Choose",
        catalog.resource_type_menu_sections(),
    )


def _ask_kind(contact: WaContact, subject: Subject, resource_type: str) -> None:
    label = catalog.RESOURCE_TYPE_LABELS.get(resource_type, resource_type)
    meta_client.send_interactive_buttons(
        contact.phone_number,
        f"{subject.course_title} — {label}. What do you need?",
        catalog.kind_menu_buttons(),
    )


def _deliver(contact: WaContact, subject: Subject, resource_type: str, kind: str) -> None:
    phone = contact.phone_number
    label = catalog.RESOURCE_TYPE_LABELS.get(resource_type, resource_type)
    kind_label = catalog.KIND_LABELS.get(kind, kind)
    rows = list(catalog.resources_for(subject, resource_type, kind))

    if not rows:
        meta_client.send_text(
            phone,
            f"No {kind_label.lower()} found yet for {subject.course_title} — {label}. "
            "Ask your department admin to upload it, or try a different unit or kind.",
        )
        return

    if kind == ContentKind.NOTES:
        meta_client.send_text(phone, f"Here's the {label.lower()} notes for {subject.course_title}:")
        for resource in rows:
            if not resource.file:
                continue
            try:
                handle = resource.file.open("rb")
            except (FileNotFoundError, OSError):
                meta_client.send_text(
                    phone,
                    f"⚠️ \"{resource.title}\" is listed but its file is missing — "
                    "please tell an administrator.",
                )
                continue
            try:
                filename = resource.file_name or f"{resource.title}.{resource.file_ext or 'pdf'}"
                media_id = meta_client.upload_media(
                    handle, filename, resource.file_type or "application/octet-stream"
                )
                meta_client.send_document(phone, media_id, filename, caption=resource.title)
            finally:
                handle.close()
    else:
        lines = [f"Here are the {kind_label.lower()} for {subject.course_title} — {label}:"]
        lines += [f"• {resource.title}: {resource.url}" for resource in rows]
        meta_client.send_text(phone, "\n".join(lines))

    meta_client.send_text(phone, "Ask me about another subject anytime, or type \"menu\" for help.")


# --------------------------------------------------------------------------- #
# Small parsers
# --------------------------------------------------------------------------- #


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _resolve_semester_text(department, text: str) -> Semester | None:
    low = _normalize(text)
    if low in _ROMAN_SEMESTERS:
        number = _ROMAN_SEMESTERS[low]
    else:
        match = re.search(r"\d+", low)
        if not match:
            return None
        number = int(match.group(0))
    return Semester.objects.filter(department=department, semester_number=number).first()


def _resolve_shortlist_pick(contact: WaContact, low_text: str) -> Subject | None:
    candidates = contact.context.get("candidates") or []
    match = re.fullmatch(r"\d+", low_text)
    if not match:
        return None
    index = int(match.group(0)) - 1
    if not (0 <= index < len(candidates)):
        return None
    return Subject.objects.filter(pk=candidates[index]).first()
