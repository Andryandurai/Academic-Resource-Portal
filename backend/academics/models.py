"""Academic catalogue: Department -> Semester -> Subject.

The Department layer exists so other departments can be added later without
restructuring anything; only AI&DS is populated today.
"""

from __future__ import annotations

from django.db import models


class CourseCategory(models.TextChoices):
    """Category codes as the syllabi print them.

    Departments do not spell these identically — the same humanities course is
    filed as HS in one syllabus, HSMC in another and HSM in a third. Each is
    kept verbatim rather than normalised, because the category is published
    academic data and rewriting it would misreport the syllabus.

    MC ("Mandatory Course") appears here as a *category*, which is distinct from
    the mandatory/non-credit courses the portal excludes. Inclusion is decided by
    the syllabus section heading, never by this field: Mechatronics lists
    GE23117 under Theory Courses with an MC category, so it is included.
    """

    HS = "HS", "Humanities & Social Sciences"
    HSMC = "HSMC", "Humanities, Social Sciences & Management"
    HSM = "HSM", "Humanities & Management"
    MC = "MC", "Mandatory Course"
    MS = "MS", "Management Studies"
    BS = "BS", "Basic Sciences"
    ES = "ES", "Engineering Sciences"
    PC = "PC", "Professional Core"
    OE = "OE", "Open Elective"
    PE = "PE", "Professional Elective"


class CourseType(models.TextChoices):
    """How a course is delivered.

    Derived from the syllabus grouping first and from L/T/P only as a fallback:
    L>0 P=0 is theory, L>0 P>0 is theory plus practical, L=0 P>0 is a standalone
    laboratory.

    There is deliberately no value for non-credit, employability (EEC), soft
    skills, internship or project courses — those are outside the academic
    resource system, so there is no bucket for one to be filed under by mistake.
    """

    THEORY = "THEORY", "Theory"
    LAB_ORIENTED_THEORY = "LAB_ORIENTED_THEORY", "Lab-Oriented Theory"
    LABORATORY = "LABORATORY", "Laboratory"


class Department(models.Model):
    """A department of the college.

    The root of the academic hierarchy: every semester, subject and resource
    reaches a department through a foreign key, which is what keeps one
    department's material from ever appearing under another. Departments differ
    in structure — nothing here assumes eight semesters or a shared course
    catalogue — so a department with no curriculum yet is a normal state, not an
    incomplete one.
    """

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    # Lets a department be withdrawn from the selection list without deleting it
    # and cascading away whatever curriculum it holds.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Alphabetical by name: the selection page lists departments the way a
        # prospectus does, not by an abbreviation the student may not know.
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    # Deliberately no `has_curriculum` property: the API annotates a field of
    # that name onto the queryset, and a model property would shadow it — Django
    # cannot assign an annotation over a property with no setter, which raises
    # at serialization time. Call `curriculum_exists()` for the one-off check.
    def curriculum_exists(self) -> bool:
        """Whether any subject has been published for this department yet."""
        return Subject.objects.filter(semester__department=self).exists()


class Semester(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="semesters")
    semester_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["semester_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "semester_number"], name="uniq_department_semester"
            )
        ]

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    """A theory or lab-oriented theory course.

    `course_code` is nullable and that is a data requirement, not an oversight:
    the syllabus publishes no code for Professional and Open Electives, and the
    portal must never invent one.
    """

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="subjects")
    # Not globally unique. Departments legitimately share course codes — a first
    # year runs the same HS23111, GE23131 and GE23111 across AI&DS, AI&ML and
    # EEE — so uniqueness is scoped to the semester (see Meta.constraints).
    course_code = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    course_title = models.CharField(max_length=200)
    category = models.CharField(max_length=4, choices=CourseCategory.choices, db_index=True)
    course_type = models.CharField(max_length=24, choices=CourseType.choices, db_index=True)

    # L/T/P are weekly period counts; credits feed GPA/CGPA.
    l = models.PositiveSmallIntegerField("theory periods (L)", default=0)
    t = models.PositiveSmallIntegerField("tutorial periods (T)", default=0)
    p = models.PositiveSmallIntegerField("practical periods (P)", default=0)
    credits = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["semester__semester_number", "course_type", "course_code", "course_title"]
        indexes = [models.Index(fields=["semester", "course_type"])]
        constraints = [
            # One course code per semester. Electives carry no code at all, so
            # the constraint skips NULLs rather than colliding on them.
            models.UniqueConstraint(
                fields=["semester", "course_code"],
                condition=models.Q(course_code__isnull=False),
                name="uniq_semester_course_code",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course_code or '(no code)'} — {self.course_title}"
