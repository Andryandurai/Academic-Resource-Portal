"""The college's departments.

The canonical list, kept as data rather than scattered through the frontend so
adding or renaming a department is a database change, not a code change.

Only the department *records* live here. Curriculum — semesters, subjects,
resources — is supplied per department and seeded separately; a department with
none yet is a normal state.
"""

from __future__ import annotations

# (name, code, group)
#
# `group` drives the optional filter on the selection page. It is a display
# convenience only: nothing in the data model depends on it, so regrouping a
# department later has no effect on its curriculum.
DEPARTMENTS: tuple[tuple[str, str, str], ...] = (
    ("Aeronautical Engineering", "AE", "Engineering"),
    ("Artificial Intelligence and Data Science", "AI&DS", "Computing"),
    ("Artificial Intelligence and Machine Learning", "AI&ML", "Computing"),
    ("Automobile Engineering", "AUTO", "Engineering"),
    ("Biomedical Engineering", "BME", "Engineering"),
    ("Biotechnology", "BT", "Sciences"),
    ("Chemical Engineering", "CHEM", "Engineering"),
    # "CIVIL" rather than "CE": the department's own syllabus uses it, and CE is
    # also the course-code prefix, which made the two easy to confuse.
    ("Civil Engineering", "CIVIL", "Engineering"),
    ("Computer Science and Business Systems", "CSBS", "Computing"),
    ("Computer Science and Design", "CSD", "Computing"),
    ("Computer Science and Engineering", "CSE", "Computing"),
    ("Computer Science and Engineering (Cyber Security)", "CSE-CS", "Computing"),
    ("Electrical and Electronics Engineering", "EEE", "Engineering"),
    ("Electronics and Communication Engineering", "ECE", "Engineering"),
    ("Food Technology", "FT", "Sciences"),
    ("Information Technology", "IT", "Computing"),
    ("Mechanical Engineering", "ME", "Engineering"),
    ("Mechatronics", "MCT", "Engineering"),
    ("Robotics and Automation", "RA", "Engineering"),
)

DEPARTMENT_COUNT = len(DEPARTMENTS)

# The department whose curriculum is already populated. Matched by code so a
# name correction never orphans the existing semesters and subjects.
SEEDED_DEPARTMENT_CODE = "AI&DS"
