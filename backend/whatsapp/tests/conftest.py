from __future__ import annotations

import pytest

from academics.models import CourseCategory, CourseType, Department, Semester, Subject

from whatsapp.models import ConversationState, WaContact
from whatsapp.services import meta_client


@pytest.fixture(autouse=True)
def dry_run_and_clean_outbox(settings):
    """Every WhatsApp test sends through the dry-run outbox, never the network.

    The outbox is process-global (see meta_client._dry_run_outbox), so it is
    cleared before each test to keep tests from seeing another test's sends.
    """
    settings.WHATSAPP_DRY_RUN = True
    meta_client._dry_run_outbox.clear()
    yield
    meta_client._dry_run_outbox.clear()


@pytest.fixture
def ready_contact(curriculum, data_structures):
    """A contact past onboarding: department and semester already chosen."""
    return WaContact.objects.create(
        phone_number="911234500001",
        department=curriculum,
        semester=data_structures.semester,
        state=ConversationState.IDLE,
    )


@pytest.fixture
def ambiguous_semester(db):
    """Two subjects close enough in name that resolution must ask, not guess.

    Its own department, deliberately not the shared `department`/`curriculum`
    fixture: that one already seeds all 8 semesters of AI&DS, and a second
    semester 3 there would collide on the (department, semester_number)
    constraint.
    """
    dept = Department.objects.create(name="Ambiguous Test Department", code="AMBIG-TEST")
    semester = Semester.objects.create(department=dept, semester_number=1, name="Semester I")
    common = dict(
        semester=semester,
        category=CourseCategory.BS,
        course_type=CourseType.THEORY,
        l=3, t=0, p=0, credits=3,
    )
    maths_1 = Subject.objects.create(course_title="Engineering Mathematics I", **common)
    maths_2 = Subject.objects.create(course_title="Engineering Mathematics II", **common)
    Subject.objects.create(course_title="Engineering Physics", **common)
    return semester, maths_1, maths_2
