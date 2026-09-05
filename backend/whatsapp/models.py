"""State for the WhatsApp bot.

Two tables only. `WaContact` is one row per phone number: which department and
semester that student belongs to (asked once, at onboarding) and where the
current conversation is in the menu tree. `WaMessageLog` exists purely for
idempotency — Meta redelivers a webhook it didn't get a fast enough 200 for,
and without a record of message ids already handled a slow reply would be
sent twice.
"""

from __future__ import annotations

from django.db import models


class ConversationState(models.TextChoices):
    """Where a phone number sits in the menu tree.

    Only four states exist. Deciding whether a subject, then a unit, then a
    content kind is still needed is *not* separate state — it falls out of
    which keys are already set in `context`, re-checked on every turn — so a
    student who abandons a half-finished menu and asks about something else
    entirely is never stuck waiting for a button click that never comes.

    A dedicated state exists only where a bare digit is genuinely ambiguous
    without one: "3" means semester 3 during onboarding and "pick candidate 3"
    during a subject shortlist, both of which collide with "3" meaning Unit 3
    everywhere else. `IDLE` is the resting state once onboarding is done, and
    the state every completed or abandoned lookup returns to.
    """

    AWAITING_DEPARTMENT = "AWAITING_DEPARTMENT", "Awaiting department"
    AWAITING_SEMESTER = "AWAITING_SEMESTER", "Awaiting semester"
    AWAITING_SUBJECT_CHOICE = "AWAITING_SUBJECT_CHOICE", "Awaiting subject choice"
    IDLE = "IDLE", "Idle"


class WaContact(models.Model):
    """A phone number the bot has exchanged messages with.

    `phone_number` is WhatsApp's `wa_id` — digits only, country code included,
    no leading `+` (that is the form Meta sends and expects back).
    """

    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    display_name = models.CharField(max_length=120, blank=True, default="")

    department = models.ForeignKey(
        "academics.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    semester = models.ForeignKey(
        "academics.Semester", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    state = models.CharField(
        max_length=32, choices=ConversationState.choices, default=ConversationState.AWAITING_DEPARTMENT
    )
    # Short-lived scratch space for the state machine — e.g. the subject a
    # question resolved to while the bot waits to hear which unit, or the
    # shortlist of subjects a fuzzy match could not narrow to one. Cleared back
    # to {} every time the conversation returns to IDLE.
    context = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at"]

    def __str__(self) -> str:
        return self.phone_number

    def reset_to_idle(self) -> None:
        self.state = ConversationState.IDLE
        self.context = {}


class WaMessageLog(models.Model):
    """One row per inbound Meta message id, so a redelivered webhook is a no-op."""

    message_id = models.CharField(max_length=128, unique=True)
    contact = models.ForeignKey(WaContact, on_delete=models.CASCADE, related_name="messages")
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.message_id
