"""Per-department curricula.

Each department's syllabus is reproduced verbatim: course codes, titles,
categories and L/T/P/C are not adjusted, and no code is invented where the
syllabus leaves one blank or gives a placeholder.

Scope: Theory, Lab-Oriented Theory (theory + practical) and Laboratory courses.
Non-credit courses, employability enhancement (EEC) courses, soft skills,
internships and project phases are excluded by design — each exclusion is
recorded in `EXCLUDED` so the omission is auditable rather than silent.

Adding a department later means adding an entry here and re-running
`manage.py seed_academics`. No application code changes.
"""

from __future__ import annotations

THEORY = "THEORY"
LAB = "LAB_ORIENTED_THEORY"
LABORATORY = "LABORATORY"

# A subject is (course_code, course_title, category, course_type, L, T, P, C).
# `course_code` is None wherever the syllabus publishes no real code — for
# electives, and for placeholders such as "EE23P**" which denote "any code in
# this series" rather than an actual course.
Subject = tuple

AIDS_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23116", "Mathematical Foundations for AI", "BS", THEORY, 3, 1, 0, 4),
            ("GE23117", "தமிழ் மொழி / Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("PH23132", "Physics for Information Science", "BS", LAB, 3, 0, 2, 4),
            ("GE23131", "Programming using C", "PC", LAB, 1, 0, 6, 4),
            ("EE23133", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23214", "Probability and Inferential Statistics", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "தமிழ் மொழி / Tamil and Its Technology", "HS", THEORY, 1, 0, 0, 1),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("IT23231", "Digital Principles and Computer Architecture", "PC", LAB, 3, 1, 2, 4),
            ("AI23231", "Principles of Artificial Intelligence", "ES", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23313", "Discrete Mathematics for AI", "BS", THEORY, 3, 1, 0, 4),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23333", "Object Oriented Programming Using JAVA", "PC", LAB, 1, 0, 6, 4),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23434", "Optimization Techniques for AI", "BS", LAB, 3, 0, 2, 4),
            ("AI23431", "Web Technology and Mobile Application", "PC", LAB, 1, 0, 4, 3),
            ("AD23431", "Statistical Analysis and Computing", "PC", LAB, 2, 0, 2, 3),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("AD23531", "Big Data Architecture", "PC", LAB, 3, 0, 2, 4),
            ("AD23532", "Principles of Data Science", "PC", LAB, 2, 0, 4, 4),
            ("AI23531", "Deep Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 4, 5),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("AD23631", "Data Privacy and Security", "PC", LAB, 3, 0, 2, 4),
            ("AD23632", "Framework for Data and Visual Analytics", "PC", LAB, 3, 0, 2, 4),
            ("CS23634", "Fundamentals of Generative AI and Prompt Engineering", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            ("AI23712", "Reinforcement Learning", "PC", THEORY, 3, 0, 0, 3),
            ("CS23633", "Cloud Computing", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

AIML_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23116", "Mathematical Foundations for AI", "BS", THEORY, 3, 1, 0, 4),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("GE23111", "Engineering Graphics", "ES", LABORATORY, 0, 0, 4, 4),
            (
                "GE23122",
                "Engineering Practices - Electrical and Electronics",
                "ES",
                LABORATORY,
                0, 0, 2, 1,
            ),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23214", "Probability and Inferential Statistics", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("IT23231", "Digital Principles and Computer Architecture", "PC", LAB, 3, 0, 2, 4),
            ("AI23231", "Principles of Artificial Intelligence", "PC", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS",
                LABORATORY,
                0, 0, 2, 1,
            ),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
            ("CS23221", "Python Programming Lab", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23313", "Discrete Mathematics for AI", "BS", THEORY, 3, 1, 0, 4),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23333", "Object Oriented Programming using Java", "PC", LAB, 1, 0, 6, 4),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23434", "Optimization Techniques for AI", "BS", LAB, 3, 0, 2, 4),
            ("AI23431", "Web Technology and Mobile Application", "PC", LAB, 1, 0, 4, 3),
            ("AD23431", "Statistical Analysis and Computing", "PC", LAB, 2, 0, 2, 3),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("AD23531", "Big Data Architecture", "PC", LAB, 3, 0, 2, 4),
            ("AD23532", "Principles of Data Science", "PC", LAB, 2, 0, 4, 4),
            ("AI23531", "Deep Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 4, 5),
            (
                "AI23521",
                "Build and Deploy Machine Learning Applications",
                "PC",
                LABORATORY,
                0, 0, 2, 1,
            ),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("AI23631", "Predictive and Prescriptive Analytics", "PC", LAB, 3, 0, 2, 4),
            ("AI23632", "Natural Language Processing", "PC", LAB, 3, 0, 2, 4),
            ("CS23634", "Fundamentals of Generative AI and Prompt Engineering", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            ("AI23711", "Social and Ethical Issues in AI", "PC", THEORY, 3, 0, 0, 3),
            ("AI23712", "Reinforcement Learning", "PC", THEORY, 3, 0, 0, 3),
            ("IT23731", "Cloud and Big Data Architecture", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

EEE_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("GE23111", "Engineering Graphics", "ES", LABORATORY, 0, 0, 4, 4),
            (
                "GE23122",
                "Engineering Practices - Electrical and Electronics",
                "ES",
                LABORATORY,
                0, 0, 2, 1,
            ),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS",
                LABORATORY,
                0, 0, 2, 1,
            ),
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("PH23232", "Physics for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "ES", LAB, 3, 0, 4, 5),
            ("EE23211", "Electric Circuits", "PC", THEORY, 3, 0, 0, 3),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("EE23221", "Electric Circuits Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("EE23311", "Electromagnetic Theory", "ES", THEORY, 3, 0, 0, 3),
            ("EE23312", "Electrical Machines - I", "PC", THEORY, 3, 0, 0, 3),
            ("EE23313", "Measurements and Instrumentation", "PC", THEORY, 3, 0, 0, 3),
            ("EE23314", "Electronic Devices and Circuits", "PC", THEORY, 3, 0, 0, 3),
            ("EE23315", "Power Plant Engineering", "ES", THEORY, 3, 0, 0, 3),
            ("EE23321", "Electronic Devices and Circuits Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
            ("CS23336", "Introduction to Python Programming", "ES", LAB, 1, 0, 4, 3),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("EE23411", "Electrical Machines - II", "PC", THEORY, 3, 0, 0, 3),
            ("EE23412", "Transmission and Distribution", "PC", THEORY, 3, 0, 0, 3),
            ("EE23431", "Digital Logic Circuits", "PC", LAB, 3, 0, 2, 4),
            ("EE23432", "Linear Integrated Circuits and Applications", "PC", LAB, 3, 0, 2, 4),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("EE23421", "Electrical Machines Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("EE23511", "Power System Analysis", "PC", THEORY, 3, 0, 0, 3),
            ("EE23512", "Power Electronics", "PC", THEORY, 3, 0, 0, 3),
            ("EE23513", "Control Systems", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective I", "PE", THEORY, 3, 0, 0, 3),
            (
                "EE23531",
                "Microprocessors, Microcontrollers and Applications",
                "PC",
                LAB,
                3, 0, 2, 4,
            ),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("EE23521", "Electrical and Instrumentation Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("EE23611", "Protection and Switchgear", "PC", THEORY, 3, 0, 0, 3),
            ("EE23612", "Solid State Drives", "PC", THEORY, 3, 0, 0, 3),
            ("EE23613", "Electric Energy Utilization and Conservation", "PC", THEORY, 3, 0, 0, 3),
            ("EE23631", "Applications of IoT in Electrical Engineering", "PC", LAB, 2, 0, 2, 3),
            (None, "Professional Elective II", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective III", "PE", THEORY, 3, 0, 0, 3),
            ("EE23621", "Power Electronics and Drives Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            ("EE23711", "Smart Grid", "PC", THEORY, 3, 0, 0, 3),
            ("EE23712", "Power System Operation and Control", "PC", THEORY, 3, 0, 0, 3),
            ("EE23731", "Renewable Energy Systems", "PC", LAB, 3, 0, 2, 4),
            (None, "Professional Elective IV", "PE", THEORY, 3, 0, 0, 3),
            ("EE23721", "Power System Simulation Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

BME_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            # Listed under "Theory Courses" but carries 4 practical periods, so
            # it is filed as lab-oriented — see the note on classification below.
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("GE23117", "Heritage of Tamils", "BS", THEORY, 1, 0, 0, 1),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("ME23211", "Engineering Mechanics for Biomedical Engineers", "ES", THEORY, 3, 1, 0, 4),
            ("GE23217", "Heritage of Tamils and Technology", "BS", THEORY, 1, 0, 0, 1),
            ("CY23233", "Fundamentals of Data Structures using C", "ES", LAB, 3, 0, 4, 5),
            ("PH23231", "Physics for Bioscience", "BS", LAB, 3, 0, 2, 4),
            ("BM23231", "Electric Circuits and Machines", "ES", LAB, 3, 0, 2, 4),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("BM23311", "Human Anatomy and Physiology", "PC", THEORY, 3, 0, 0, 3),
            ("BM23312", "Biomedical Instrumentation", "PC", THEORY, 3, 0, 0, 3),
            ("BM23313", "Biological Science", "PC", THEORY, 3, 0, 0, 3),
            ("BM23331", "Electronic Devices and Circuits", "PC", LAB, 3, 0, 2, 4),
            ("BM23332", "Sensors and Measurements", "PC", LAB, 2, 0, 2, 3),
            ("BM23321", "Biochemistry and Physiology Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("BM23322", "Biomedical Instrumentation Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("BM23411", "Analog and Digital Integrated Circuits", "PC", THEORY, 3, 0, 0, 3),
            ("BM23412", "Communication Systems and Standards", "PC", THEORY, 3, 0, 0, 3),
            ("OE1", "Open Elective I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23436", "Probability and Random Processes", "BS", LAB, 3, 0, 2, 4),
            ("BM23431", "Pathology and Microbiology", "PC", LAB, 2, 0, 2, 3),
            ("CS23336", "Introduction to Python Programming", "ES", LAB, 1, 0, 4, 3),
            (
                "BM23421",
                "Analog and Digital Integrated Circuits Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
            ("BM23422", "PCB Design Laboratory", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("BM23511", "Biocontrol Systems", "PC", THEORY, 3, 0, 0, 3),
            ("BM23512", "Diagnostic and Therapeutic Equipment", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective II", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective I", "PE", THEORY, 3, 0, 0, 3),
            ("BM23531", "Signals and Systems Analysis", "PC", LAB, 1, 1, 2, 3),
            ("BM23532", "Microcontroller and Embedded System Design", "PC", LAB, 3, 0, 2, 4),
            # Listed under lab-integrated theory but has no lecture hours.
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
            (
                "BM23521",
                "Diagnostic and Therapeutic Equipment Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("BM23611", "Radiological Equipment", "PC", THEORY, 3, 0, 0, 3),
            ("BM23612", "Biomechanics", "PC", THEORY, 3, 1, 0, 4),
            (None, "Professional Elective II", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective III", "PE", THEORY, 3, 0, 0, 3),
            ("BM23631", "Biosignal Processing", "PC", LAB, 1, 1, 2, 3),
            ("BM23632", "Physiological Modeling Laboratory", "PC", LAB, 1, 0, 2, 2),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective IV", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective VI", "PE", THEORY, 3, 0, 0, 3),
            ("BM23731", "Medical Image Processing", "PC", LAB, 2, 1, 2, 4),
        ],
    },
    8: {
        "name": "Semester VIII",
        # The syllabus repeats Professional Electives V and VI here; reproduced
        # as supplied rather than silently deduplicated against Semester VII.
        "subjects": [
            (None, "Professional Elective V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

CIVIL_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23112", "Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("CE23111", "Building Materials", "PC", THEORY, 3, 0, 0, 3),
            # Under "Theory Courses" but carries 4 practical periods.
            ("CE23112", "Engineering Drawing for Civil", "PC", LAB, 2, 0, 4, 4),
            ("PH23131", "Physics of Materials", "BS", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("GE23111", "Engineering Mechanics", "ES", THEORY, 2, 1, 0, 3),
            ("CY23233", "Engineering Chemistry", "BS", LAB, 3, 0, 2, 4),
            ("EE23313", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
            ("GE23231", "Programming Using Python", "ES", LAB, 1, 0, 4, 3),
            (
                "CE23221",
                "Computer Aided Building Drawing for Civil Engineers",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("CE23311", "Strength of Materials I", "PC", THEORY, 3, 0, 0, 3),
            ("CE23312", "Fluid Mechanics", "PC", THEORY, 3, 0, 0, 3),
            (
                "CE23313",
                "Construction Techniques, Equipment and Practice",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            ("CE23331", "Surveying", "PC", LAB, 3, 0, 2, 4),
            ("MA23331", "Transforms and Statistics", "BS", LAB, 3, 0, 2, 4),
            ("CE23321", "Construction Materials Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("CE23411", "Strength of Materials II", "PC", THEORY, 3, 0, 0, 3),
            ("CE23412", "Hydraulics and Irrigation Structures", "PC", THEORY, 3, 0, 0, 3),
            ("CE23413", "Water Supply Engineering", "PC", THEORY, 3, 0, 0, 3),
            ("CE23414", "Highway and Railway Engineering", "PC", THEORY, 3, 0, 0, 3),
            ("CE23431", "Soil Mechanics", "PC", LAB, 3, 0, 2, 4),
            (None, "Open Elective I", "OE", THEORY, 3, 0, 0, 3),
            (
                "CE23421",
                "Strength of Materials and Hydraulic Engineering Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("CE23511", "Design of Reinforced Concrete Elements", "PC", THEORY, 3, 1, 0, 4),
            ("CE23512", "Foundation Engineering", "PC", THEORY, 3, 0, 0, 3),
            ("CE23513", "Waste Water Engineering", "PC", THEORY, 3, 0, 0, 3),
            ("CE23531", "Structural Analysis", "PC", LAB, 3, 0, 2, 4),
            (None, "Professional Elective I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective II", "OE", THEORY, 3, 0, 0, 3),
            (
                "CE23521",
                "Water and Waste Water Analysis Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
            ("CE23522", "Survey Camp", "PC", LABORATORY, 0, 0, 2, 1),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("CE23611", "Design of Steel Structures", "PC", THEORY, 3, 1, 0, 4),
            (
                "CE23612",
                "Construction, Planning, Scheduling and Management",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            (
                "CE23613",
                "Structural Dynamics and Earthquake Engineering",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            (None, "Professional Elective II", "PE", THEORY, 3, 0, 0, 3),
            ("CE23631", "Structural Design and Drawing", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (
                "CE23711",
                "Estimation, Costing and Valuation Engineering",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            ("CE23712", "Hydrology", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective IV", "PE", THEORY, 3, 0, 0, 3),
            ("CE23721", "Building Information Modelling", "PC", LABORATORY, 0, 0, 4, 2),
            # Included deliberately: its category is BS, but the syllabus lists
            # it under Laboratory Courses. Category is not the filter.
            (
                "CE23723",
                "Artificial Intelligence and Machine Learning for Civil Engineers",
                "BS", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

CSE_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("EE23133", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
            ("PH23132", "Physics for Information Science", "BS", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23213", "Discrete Mathematical Structures", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("EC23232", "Digital Logic and Microprocessor", "ES", LAB, 3, 0, 2, 4),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
            ("CS23221", "Python Programming Lab", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("CS23311", "Computer Architecture", "PC", THEORY, 3, 0, 0, 3),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23333", "Object Oriented Programming Using Java", "PC", LAB, 1, 0, 6, 4),
            ("CS23334", "Fundamentals of Data Science", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            (None, "Open Elective - I", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("MA23435", "Probability, Statistics and Simulation", "BS", LAB, 3, 0, 2, 4),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("CS23511", "Theory of Computation", "PC", THEORY, 3, 1, 0, 4),
            ("CS23512", "Fundamentals of Mobile Computing", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("CS23531", "Web Programming", "PC", LAB, 1, 0, 6, 4),
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 4, 5),
            ("CS23533", "Foundations of Artificial Intelligence", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("CS23631", "Compiler Design", "PC", LAB, 3, 0, 2, 4),
            ("CS23632", "Cryptography and Network Security", "PC", LAB, 2, 0, 2, 3),
            ("CS23633", "Cloud Computing", "PC", LAB, 2, 0, 2, 3),
            ("CS23634", "Fundamentals of Generative AI and Prompt Engineering", "PC", LAB, 2, 0, 2, 3),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23621", "Mobile Application Development Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-VII", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

ECE_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("EC23131", "Electronic Devices", "PC", LAB, 3, 0, 2, 4),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            # Listed under Theory Courses but carries 4 practical periods.
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("EE23232", "Basic Electrical Engineering", "ES", LAB, 3, 0, 2, 4),
            ("PH23232", "Physics for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("EC23311", "Analog Circuits-I", "PC", THEORY, 3, 0, 0, 3),
            ("EE23312", "Electromagnetic Fields", "PC", THEORY, 3, 0, 0, 3),
            ("EC23313", "Digital Principles and System Design", "PC", THEORY, 3, 0, 0, 3),
            (
                "EC23332",
                "Principles of Microprocessors and Microcontrollers",
                "PC", LAB, 3, 0, 2, 4,
            ),
            ("CS23336", "Introduction to Python Programming", "ES", LAB, 1, 0, 4, 3),
            ("EC23321", "Analog and Digital Circuits Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("EC23411", "Signals and Systems", "PC", THEORY, 3, 0, 0, 3),
            ("EC23412", "Transmission Lines and Waveguides", "PC", THEORY, 3, 0, 0, 3),
            ("EC23413", "Communication Theory", "PC", THEORY, 3, 0, 0, 3),
            ("EC23431", "Analog Electronics", "PC", LAB, 3, 0, 2, 4),
            ("MA23436", "Probability and Random Processes", "BS", LAB, 3, 0, 2, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("EC23511", "Control System Engineering", "PC", THEORY, 2, 1, 0, 3),
            ("EC23512", "Modern Digital Communication", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("EC23531", "Digital Signal Processing", "PC", LAB, 3, 0, 2, 4),
            ("EC23521", "Communication Systems Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("EC23611", "Antenna Theory and Wave Propagation", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("EC23631", "VLSI and Chip Design", "PC", LAB, 3, 0, 2, 4),
            ("EC23632", "Communication Networks", "PC", LAB, 3, 0, 2, 4),
            ("EC23633", "Wireless Communication", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            ("EC23731", "Optical Communication and Networks", "PC", LAB, 2, 0, 2, 3),
            ("EC23732", "RF and Microwave Engineering", "PC", LAB, 2, 0, 2, 3),
            ("EC23733", "Embedded and Real Time Systems", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

CSD_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            # CSD runs MA23111 as "Mathematics for Design"; CSE and ECE run the
            # same code as "Linear Algebra and Calculus". Reproduced per syllabus.
            ("MA23111", "Mathematics for Design", "BS", THEORY, 3, 1, 0, 4),
            ("CD23111", "Design Drawing and Sketching", "PC", THEORY, 2, 1, 0, 3),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("PH23132", "Physics for Information Science", "BS", LAB, 3, 0, 2, 4),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23214", "Probability and Inferential Statistics", "BS", THEORY, 3, 1, 0, 4),
            ("CD23211", "Foundation in Digital Storytelling", "PC", THEORY, 3, 0, 0, 3),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("CD23231", "Visual Communication Foundations", "PC", LAB, 2, 0, 4, 4),
            ("IT23231", "Digital Principles and Computer Architecture", "PC", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23313", "Discrete Mathematics for AI", "BS", THEORY, 3, 1, 0, 4),
            ("CD23331", "Design Processes and Perspectives", "PC", LAB, 3, 0, 2, 4),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
            ("CD23332", "UI and UX Design", "PC", LAB, 2, 0, 4, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CD23321", "Python Programming for Design", "PC", LABORATORY, 0, 0, 6, 3),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23433", "Mathematical Modelling and Simulation", "BS", LAB, 3, 0, 2, 4),
            ("AI23231", "Principles of Artificial Intelligence", "PC", LAB, 3, 0, 2, 4),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 2, 4),
            ("CS23333", "Object Oriented Programming using Java", "PC", LAB, 1, 0, 6, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("CD23531", "3D Modelling and Texturing", "PC", LAB, 2, 0, 2, 3),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23531", "Web Programming", "PC", LAB, 1, 0, 6, 4),
            ("IT23E31", "Graphics and Multimedia", "PE", LAB, 2, 0, 2, 3),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            # This elective is lab-oriented in CSD, unlike the theory-only
            # electives elsewhere — it carries 2 practical periods.
            (None, "Professional Elective-II", "PE", LAB, 3, 0, 2, 3),
            ("CD23631", "Game Design and Development", "PC", LAB, 2, 0, 4, 4),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            (
                "CD23621",
                "Mobile Application Design and Development Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", LAB, 2, 0, 4, 3),
            ("CD23731", "Film Making and Radio Podcasting", "PC", LAB, 2, 0, 2, 3),
            ("CD23721", "Visual Effects", "PC", LABORATORY, 0, 0, 6, 3),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

ME_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23112", "Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            # Listed under Theory but carries 4 practical periods.
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("EC23111", "Basic Electronics Engineering", "ES", THEORY, 3, 0, 0, 3),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("PH23131", "Physics of Materials", "BS", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices - Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            # Listed under Theory but has no lecture hours — a practical.
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            # ME runs GE23111 as Engineering Mechanics in Semester II, separate
            # from the Semester I Engineering Graphics record.
            ("GE23111", "Engineering Mechanics", "ES", THEORY, 2, 1, 0, 3),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("CY23233", "Engineering Chemistry", "BS", LAB, 3, 0, 2, 4),
            ("EE23132", "Basic Electrical Engineering", "ES", LAB, 3, 0, 2, 4),
            ("GE23233", "Problem Solving with Python Programming", "ES", LAB, 2, 0, 4, 4),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("ME23311", "Engineering Thermodynamics", "PC", THEORY, 3, 1, 0, 4),
            ("ME23312", "Manufacturing Technology I", "PC", THEORY, 3, 0, 0, 3),
            ("ME23313", "Kinematics of Machinery", "PC", THEORY, 3, 0, 0, 3),
            ("MA23331", "Transforms and Statistics", "BS", LAB, 3, 0, 2, 4),
            ("ME23331", "Strength of Materials", "PC", LAB, 3, 0, 2, 4),
            ("ME23321", "Manufacturing Technology Laboratory I", "PC", LABORATORY, 0, 0, 2, 1),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("ME23411", "Engineering Materials and Metallurgy", "PC", THEORY, 3, 0, 0, 3),
            ("ME23412", "Manufacturing Technology II", "PC", THEORY, 3, 0, 0, 3),
            ("ME23431", "Dynamics of Machines", "PC", LAB, 3, 0, 2, 4),
            ("ME23432", "Fluid Mechanics and Machinery", "PC", LAB, 3, 0, 2, 4),
            ("ME23433", "Thermal Engineering", "PC", LAB, 3, 0, 2, 4),
            ("ME23421", "Computer Aided Machine Drawing Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("ME23422", "Manufacturing Technology Laboratory II", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("GE23511", "Economics for Engineers", "HS", THEORY, 3, 0, 0, 3),
            ("ME23511", "Machine Design", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("ME23531", "Heat and Mass Transfer", "PC", LAB, 3, 0, 2, 4),
            ("ME23332", "Metrology and Measurements", "PC", LAB, 3, 0, 2, 4),
            ("ME23521", "Component Modeling Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("ME23611", "Additive Manufacturing", "PC", THEORY, 3, 0, 0, 3),
            ("ME23612", "Design of Transmission Systems", "PC", THEORY, 3, 0, 0, 3),
            ("ME23613", "Finite Element Analysis", "PC", THEORY, 3, 0, 0, 3),
            ("ME23614", "Total Quality Management", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("ME23631", "Robotics Laboratory", "PC", LAB, 1, 0, 2, 2),
            ("ME23622", "Simulation and Analysis Laboratory", "PC", LABORATORY, 0, 0, 3, 2),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            ("ME23711", "Process Planning and Cost Estimation", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            ("ME23731", "Artificial Intelligence for Mechanical Engineers", "PC", LAB, 2, 0, 4, 4),
            ("ME23732", "Mechatronics", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

IT_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("EE23133", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("GE23122", "Engineering Practices - Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23213", "Discrete Mathematical Structures", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "Heritage of Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("PH23132", "Physics for Information Science", "BS", LAB, 3, 0, 2, 4),
            ("EC23331", "Microprocessors and Microcontroller", "ES", LAB, 3, 0, 2, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            ("GE23121", "Engineering Practices-Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
            ("CS23221", "Python Programming Lab", "PC", LABORATORY, 0, 0, 4, 2),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("EC23314", "Analog and Digital Communication", "ES", THEORY, 3, 0, 0, 3),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23333", "Object Oriented Programming using Java", "PC", LAB, 1, 0, 6, 4),
            ("IT23331", "Digital Logic and Computer Architecture", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("GE23311", "Fundamentals of Management for Engineers", "HS", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23435", "Probability, Statistics and Simulation", "BS", LAB, 3, 0, 2, 4),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
            ("IT23431", "MongoDB Essentials", "PC", LAB, 2, 0, 2, 3),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("IT23511", "Automata Theory and Compiler Design", "PC", THEORY, 3, 0, 0, 3),
            ("IT23531", "Computer Vision", "PC", LAB, 3, 0, 2, 4),
            ("CS23531", "Web Programming", "PC", LAB, 1, 0, 6, 4),
            ("AI23231", "Principles of Artificial Intelligence", "PC", LAB, 3, 0, 2, 4),
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 4, 5),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            ("CS23512", "Fundamentals of Mobile Computing", "PC", THEORY, 3, 0, 0, 3),
            ("CS23632", "Cryptography and Network Security", "PC", LAB, 2, 0, 2, 3),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            ("CS23621", "Mobile Application Development Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            ("IT23731", "Cloud and Big Data Architecture", "PC", LAB, 3, 0, 2, 4),
            ("IT23721", "Data Science using R", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

MCT_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HSMC", THEORY, 2, 0, 0, 2),
            ("MA23112", "Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            # Listed under Theory but carries 4 practical periods.
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("RO23111", "Introduction to Mechanical Systems", "ES", THEORY, 2, 1, 0, 3),
            # Category MC, but the syllabus lists it under Theory Courses — the
            # section heading decides inclusion, not the category code.
            ("GE23117", "Heritage of Tamils", "MC", THEORY, 1, 0, 0, 1),
            ("EE23132", "Basic Electrical Engineering", "ES", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices – Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
            ("GE23122", "Engineering Practices – Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
            ("MT23121", "Computer Aided Drawing Laboratory", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("PH23131", "Physics of Materials", "BS", LAB, 3, 0, 2, 4),
            ("GE23333", "Problem Solving with Python Programming", "ES", LAB, 2, 0, 4, 4),
            ("MT23131", "Elements of Mechatronics", "ES", LAB, 2, 0, 2, 3),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HSMC", LABORATORY, 0, 0, 2, 1,
            ),
            ("RO23211", "Computer Aided Modeling Laboratory", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            (
                "MA23311",
                "Transforms and Applied Partial Differential Equations",
                "BS", THEORY, 3, 1, 0, 4,
            ),
            ("RO23311", "Analog and Digital Electronics", "PC", THEORY, 3, 0, 0, 3),
            ("MT23312", "Theory of Mechanisms and Machines-I", "PC", THEORY, 3, 1, 0, 4),
            ("RO23313", "Sensors in Automation", "PC", THEORY, 3, 0, 0, 3),
            ("RO23331", "Elements of Manufacturing Processes", "PC", LAB, 3, 0, 2, 4),
            ("RO23332", "Mechanics of Materials", "ES", LAB, 3, 0, 2, 4),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("MT23411", "Fluid Mechanics and Thermal Sciences", "PC", THEORY, 4, 0, 0, 4),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23432", "Statistics and Numerical Methods", "BS", LAB, 3, 0, 2, 4),
            ("MT23431", "Microcontrollers and Embedded Systems", "PC", LAB, 3, 0, 2, 4),
            ("MT23432", "Sensors and Instrumentation", "PC", LAB, 3, 0, 2, 4),
            ("MT23433", "System Dynamics and Control", "PC", LAB, 3, 0, 2, 4),
            ("MT23421", "Fluid Mechanics and Heat Transfer Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("GE23311", "Fundamentals of Management for Engineers", "HSM", THEORY, 3, 0, 0, 3),
            ("MT23511", "Semiconductor Manufacturing", "PC", THEORY, 3, 0, 0, 3),
            ("MT23512", "Industrial Electronics", "PC", THEORY, 3, 0, 0, 3),
            ("MT23513", "Basic Engineering Research Methods", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
            ("MT23522", "Industrial Electronics Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("MT23611", "Fundamentals of Machine Design", "PC", THEORY, 2, 1, 0, 3),
            ("MT23612", "Ethics in Robotics and Artificial Intelligence", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("MT23631", "Industrial Robotics", "PC", LAB, 2, 1, 2, 4),
            ("MT23632", "Applied Hydraulics and Pneumatics", "PC", LAB, 2, 1, 2, 4),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            ("MT23711", "Industrial Automation", "PC", THEORY, 2, 1, 0, 3),
            ("MT23712", "Machine Vision", "PC", THEORY, 3, 1, 0, 4),
            ("MT23721", "Computer Aided Engineering Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
            ("MT23722", "Industrial Automation Laboratory", "PC", LABORATORY, 0, 0, 2, 1),
            (
                "MT23723",
                "Mechatronics Engineering Problem Solving Using AI, ML and DL",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

RA_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HSMC", THEORY, 2, 0, 0, 2),
            ("MA23112", "Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("RO23111", "Introduction to Mechanical Systems", "ES", THEORY, 2, 1, 0, 3),
            ("GE23117", "Heritage of Tamils", "HSMC", THEORY, 1, 0, 0, 1),
            ("EE23132", "Basic Electrical Engineering", "ES", LAB, 3, 0, 2, 4),
            ("GE23121", "Engineering Practices – Civil and Mechanical", "ES", LABORATORY, 0, 0, 2, 1),
            ("GE23122", "Engineering Practices – Electrical and Electronics", "ES", LABORATORY, 0, 0, 2, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23212", "Differential Equations and Complex Variables", "BS", THEORY, 3, 1, 0, 4),
            ("CY23131", "Chemistry for Electronics Engineering", "BS", LAB, 3, 0, 2, 4),
            ("PH23131", "Physics of Materials", "BS", LAB, 3, 0, 2, 4),
            ("GE23333", "Problem Solving with Python Programming", "ES", LAB, 2, 0, 4, 4),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HSMC", LABORATORY, 0, 0, 2, 1,
            ),
            ("RO23211", "Computer Aided Modeling Laboratory", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            (
                "MA23311",
                "Transforms and Applied Partial Differential Equations",
                "BS", THEORY, 3, 1, 0, 4,
            ),
            ("RO23311", "Analog and Digital Electronics", "PC", THEORY, 3, 0, 0, 3),
            # RA files this under RO23312; Mechatronics uses MT23312 for the
            # same title. Separate records, per the two syllabi.
            ("RO23312", "Theory of Mechanisms and Machines-I", "PC", THEORY, 3, 1, 0, 4),
            ("RO23313", "Sensors in Automation", "PC", THEORY, 3, 0, 0, 3),
            ("RO23331", "Elements of Manufacturing Processes", "PC", LAB, 3, 0, 2, 4),
            ("RO23332", "Mechanics of Materials", "ES", LAB, 3, 0, 2, 4),
            ("CS23422", "Python Programming for Machine Learning", "ES", LABORATORY, 0, 0, 4, 2),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("RO23411", "Fluid Power Systems", "PC", THEORY, 3, 0, 0, 3),
            ("RO23412", "Industrial Automation and Control", "PC", THEORY, 3, 0, 0, 3),
            (
                "RO23413",
                "Microcontrollers and Real Time Embedded Systems",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            ("RO23414", "Robot Kinematics", "PC", THEORY, 3, 1, 0, 4),
            ("MA23432", "Statistics and Numerical Methods", "BS", LAB, 3, 0, 2, 4),
            ("RO23421", "Mechanisms and Robotics Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("RO23422", "Industrial Automation Laboratory-I", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("RO23511", "AI for Robotics", "PC", THEORY, 3, 0, 0, 3),
            ("RO23512", "Theory of Mechanisms and Machines-II", "PC", THEORY, 3, 1, 0, 4),
            ("ME23511", "Machine Design", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("RO23521", "Mobile Robotics Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            ("RO23522", "Industrial Automation Laboratory-II", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("ME23612", "Design of Transmission Systems", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            ("RO23631", "Robot Operating System", "PC", LAB, 2, 0, 2, 3),
            ("RO23632", "Robot Vision and Intelligence", "PC", LAB, 3, 0, 2, 4),
            ("RO23633", "Robot Dynamics and Motion Planning", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            ("RO23711", "Aerial Robotics", "PC", THEORY, 3, 0, 0, 3),
            ("RO23712", "Humanoid Robotics", "PC", THEORY, 3, 0, 0, 3),
            ("RO23713", "Resource Management Techniques", "HSMC", THEORY, 3, 1, 0, 4),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            (
                "RO23721",
                "Robotics and Automation Problem Solving Using AI, ML and DL",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

CSE_CS_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23111", "Linear Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
            ("GE23131", "Programming using C", "ES", LAB, 1, 0, 6, 4),
            ("EE23133", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
            ("PH23132", "Physics for Information Science", "BS", LAB, 3, 0, 2, 4),
            (
                "GE23121",
                "Engineering Practices-Civil and Mechanical",
                "ES", LABORATORY, 0, 0, 2, 1,
            ),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            ("MA23213", "Discrete Mathematical Structures", "BS", THEORY, 3, 1, 0, 4),
            ("GE23217", "Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("EC23232", "Digital Logic and Microprocessor", "ES", LAB, 3, 0, 2, 4),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            ("CS23231", "Data Structures", "PC", LAB, 3, 0, 4, 5),
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            (
                "GE23122",
                "Engineering Practices-Electrical and Electronics",
                "ES", LABORATORY, 0, 0, 2, 1,
            ),
            ("CS23221", "Python Programming Lab", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            ("MA23312", "Fourier Series and Number Theory", "BS", THEORY, 3, 1, 0, 4),
            ("CS23332", "Database Management Systems", "PC", LAB, 3, 0, 4, 5),
            ("CS23333", "Object Oriented Programming Using Java", "PC", LAB, 1, 0, 6, 4),
            # The syllabus runs Computer Networks in the third semester under the
            # fifth-semester code. Reproduced as printed; codes are not corrected.
            ("CS23532", "Computer Networks", "PC", LAB, 3, 0, 4, 5),
            ("CR23331", "Cryptography", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            ("MA23435", "Probability, Statistics and Simulation", "BS", LAB, 3, 0, 2, 4),
            ("CS23431", "Operating Systems", "PC", LAB, 3, 0, 4, 5),
            ("CR23431", "Network Security", "PC", LAB, 3, 0, 2, 4),
            ("CS23331", "Design and Analysis of Algorithms", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            (None, "Professional Elective-I", "PE", THEORY, 3, 0, 0, 3),
            ("CS23531", "Web Programming", "PC", LAB, 1, 0, 6, 4),
            ("CS23533", "Foundations of Artificial Intelligence", "PC", LAB, 3, 0, 2, 4),
            ("CR23531", "Ethical Hacking", "PC", LAB, 3, 0, 2, 4),
            ("CR23532", "Cyber and Digital Forensics", "PC", LAB, 3, 0, 2, 4),
            ("CS23432", "Software Construction", "PC", LAB, 3, 0, 2, 4),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("CR23611", "Cyber Laws and Security Policies", "PC", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-II", "PE", THEORY, 3, 0, 0, 3),
            ("CR23631", "Malware Analysis", "PC", LAB, 3, 0, 2, 4),
            ("CR23632", "Blockchain Technologies", "PC", LAB, 3, 0, 2, 4),
            ("AI23331", "Fundamentals of Machine Learning", "PC", LAB, 3, 0, 2, 4),
            (
                "CS23621",
                "Mobile Application Development Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (None, "Professional Elective-III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-IV", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective-V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            (
                "CR23731",
                "Blockchain Development in Hyperledger Fabric",
                "PC", LAB, 2, 0, 2, 3,
            ),
        ],
    },
    8: {
        "name": "Semester VIII",
        "subjects": [
            (None, "Professional Elective-VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
}

FT_CURRICULUM: dict[int, dict] = {
    1: {
        "name": "Semester I",
        "subjects": [
            ("HS23111", "Technical Communication I", "HS", THEORY, 2, 0, 0, 2),
            ("MA23112", "Algebra and Calculus", "BS", THEORY, 3, 1, 0, 4),
            ("CY23132", "Chemistry for Technologists", "BS", LAB, 3, 0, 2, 4),
            ("GE23111", "Engineering Graphics", "ES", LAB, 2, 0, 4, 4),
            (
                "GE23121",
                "Engineering Practices - Civil and Mechanical",
                "ES", LABORATORY, 0, 0, 2, 1,
            ),
            ("GE23117", "Heritage of Tamils", "HS", THEORY, 1, 0, 0, 1),
        ],
    },
    2: {
        "name": "Semester II",
        "subjects": [
            (
                "HS23221 / HS23222",
                "Technical Communication II / English for Professional Competence",
                "HS", LABORATORY, 0, 0, 2, 1,
            ),
            (
                "MA23212",
                "Differential Equation and Complex Variables",
                "BS", THEORY, 3, 1, 0, 4,
            ),
            ("EE23133", "Basic Electrical and Electronics Engineering", "ES", LAB, 3, 0, 2, 4),
            ("PH23231", "Physics for Bioscience", "BS", LAB, 3, 0, 2, 4),
            ("GE23233", "Problem Solving and Python Programming", "ES", LAB, 2, 0, 4, 4),
            ("FT23201", "Food Chemistry", "PC", THEORY, 3, 0, 0, 3),
            ("GE23217", "Tamils and Technology", "HS", THEORY, 1, 0, 0, 1),
            ("FT23211", "Food Chemistry Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
        ],
    },
    3: {
        "name": "Semester III",
        "subjects": [
            (
                "MA23311",
                "Transforms and Applied Partial Differential Equations",
                "BS", THEORY, 3, 1, 0, 4,
            ),
            ("FT23301", "Food Microbiology", "PC", THEORY, 3, 0, 0, 3),
            ("FT23302", "Biochemistry and Nutrition", "PC", THEORY, 3, 0, 0, 3),
            ("FT23303", "Thermodynamics for Food Technologists", "ES", THEORY, 3, 0, 0, 3),
            ("FT23304", "Food Process Calculations", "ES", THEORY, 3, 0, 0, 3),
            ("FT23305", "Food Additives", "PC", THEORY, 3, 0, 0, 3),
            ("FT23311", "Food Microbiology Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            (
                "FT23312",
                "Biochemistry and Nutrition Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    4: {
        "name": "Semester IV",
        "subjects": [
            ("MA23431", "Probability, Statistics and Reliability", "BS", LAB, 3, 0, 2, 4),
            ("FT23401", "Unit Operations in Food Industries", "PC", THEORY, 3, 0, 0, 3),
            (
                "FT23402",
                "Food Processing and Preservation Technology",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            ("FT23403", "Fluid Mechanics in Food Processes", "ES", THEORY, 3, 0, 0, 3),
            ("FT23404", "Refrigeration and Cold Chain Management", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-I", "OE", THEORY, 3, 0, 0, 3),
            (
                "FT23411",
                "Unit Operations in Food Industries Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
            (
                "FT23412",
                "Food Processing and Preservation Laboratory-I",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    5: {
        "name": "Semester V",
        "subjects": [
            ("FT23501", "Food Analysis", "PC", THEORY, 3, 0, 0, 3),
            ("FT23502", "Food Process Engineering", "PC", THEORY, 3, 0, 0, 3),
            (
                "FT23503",
                "Heat and Mass Transfer in Food Processing",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            # Printed without a hyphen in this syllabus ("Professional Elective I"),
            # unlike the hyphenated form other departments use. Kept as published.
            (None, "Professional Elective I", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective II", "PE", THEORY, 3, 0, 0, 3),
            ("GE23311", "Fundamentals of Management for Engineers", "HS", THEORY, 3, 0, 0, 3),
            ("FT23511", "Food Analysis Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            (
                "FT23512",
                "Food Processing and Preservation Laboratory-II",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
        ],
    },
    6: {
        "name": "Semester VI",
        "subjects": [
            ("FT23601", "Food Product Technology", "PC", THEORY, 3, 0, 0, 3),
            ("FT23602", "Food Packaging Technology", "PC", THEORY, 3, 0, 0, 3),
            (
                "FT23603",
                "Start-up Ecosystems for Food Technologists",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            (None, "Professional Elective III", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective IV", "PE", THEORY, 3, 0, 0, 3),
            (
                "FT23611",
                "Food Packaging Technology Laboratory",
                "PC", LABORATORY, 0, 0, 4, 2,
            ),
            ("FT23612", "Food Product Technology Laboratory", "PC", LABORATORY, 0, 0, 4, 2),
            (
                "FT23613",
                "Microfluidics Laboratory for Food Technology",
                "PC", LABORATORY, 0, 0, 2, 1,
            ),
        ],
    },
    7: {
        "name": "Semester VII",
        "subjects": [
            (
                "FT23701",
                "Food Quality, Safety Standards and Certification",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            (
                "FT23702",
                "Comprehension and Communication for Food Technologists",
                "PC", THEORY, 3, 0, 0, 3,
            ),
            ("FT23703", "Functional Foods and Nutraceuticals", "PC", THEORY, 3, 0, 0, 3),
            (None, "Open Elective-II", "OE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective V", "PE", THEORY, 3, 0, 0, 3),
            (None, "Professional Elective VI", "PE", THEORY, 3, 0, 0, 3),
        ],
    },
    # Semester VIII carries only FT23811 Project Work, which is an EEC course and
    # therefore excluded. The semester is still created so the department reads
    # as an eight-semester programme with an empty final term, rather than as a
    # seven-semester one — an empty semester is a normal state here.
    8: {
        "name": "Semester VIII",
        "subjects": [],
    },
}

# Keyed by department code — the only thing `seed_academics` iterates.
CURRICULA: dict[str, dict[int, dict]] = {
    "AI&DS": AIDS_CURRICULUM,
    "AI&ML": AIML_CURRICULUM,
    "EEE": EEE_CURRICULUM,
    "BME": BME_CURRICULUM,
    "CIVIL": CIVIL_CURRICULUM,
    "CSE": CSE_CURRICULUM,
    "ECE": ECE_CURRICULUM,
    "CSD": CSD_CURRICULUM,
    "ME": ME_CURRICULUM,
    "IT": IT_CURRICULUM,
    "MCT": MCT_CURRICULUM,
    "RA": RA_CURRICULUM,
    # The department record has used the code CSE-CS since the departments were
    # first seeded; the syllabus header calls it CYS. The stored code is left
    # alone so the existing record is reused rather than duplicated.
    "CSE-CS": CSE_CS_CURRICULUM,
    "FT": FT_CURRICULUM,
}

# Courses deliberately left out, recorded so the omission can be audited rather
# than mistaken for a gap. `verify_curriculum` asserts none of these was seeded.
EXCLUDED: dict[str, list[tuple[str, str, str]]] = {
    "AI&ML": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("AI23421", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23631", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("AI23721", "Project Phase-I", "EEC"),
        ("AI23821", "Project Phase-II", "EEC"),
    ],
    "EEE": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("EE23622", "Applications of AI and ML in Electrical Engineering", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("EE23722", "Project Work Phase I", "EEC"),
        ("EE23723", "Internship", "EEC"),
        ("EE23821", "Project Work Phase II", "EEC"),
    ],
    "BME": [
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("BM23621", "Medical Industrial Training", "EEC"),
        ("BM23711", "Comprehension in Biomedical Engineering", "EEC"),
        (
            "BM23721",
            "Artificial Intelligence and Machine Learning for Biomedical Engineering",
            "EEC",
        ),
        ("BM23722", "Project Phase-I", "EEC"),
        ("BM23723", "Hospital Training", "EEC"),
        ("BM23821", "Project Phase-II", "EEC"),
    ],
    "CIVIL": [
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("CE23722", "Design Project", "EEC"),
        ("CE23724", "Internship", "EEC"),
        ("CE23821", "Project Work", "EEC"),
    ],
    "CSE": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("CS23421", "Internship (2 weeks)", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("CS23721", "Project Phase I", "EEC"),
        ("CS23821", "Project Phase II", "EEC"),
    ],
    "ECE": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("EC23522", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        (
            "EC23721",
            "Artificial Intelligence and Machine Learning for Electronic Engineering",
            "EEC",
        ),
        ("EC23821", "Project Work", "EEC"),
    ],
    "CSD": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("CD23421", "Industry Internship (2/4 weeks)", "EEC"),
        ("GE23627", "Design Thinking for Innovation", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("CD23632", "3D Rigging and Animation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("CD23722", "Capstone Project Phase 1", "EEC"),
        ("CD23821", "Capstone Project Phase 2", "EEC"),
    ],
    "ME": [
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("ME23522", "Industrial Training Internship", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("ME23623", "Innovation and Design Thinking for Mechanical Engineer", "EEC"),
        ("ME23721", "Comprehension", "EEC"),
        ("ME23723", "Project Phase I", "EEC"),
        ("ME23821", "Project Work", "EEC"),
    ],
    "MCT": [
        ("MC23112", "Environmental Science and Engineering", "Mandatory"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Mandatory"),
        ("GE23217", "Heritage of Tamils and Technology", "Mandatory"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("MT23523", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("MT23724", "Project Work I", "EEC"),
        ("MT23821", "Project Work Phase II", "EEC"),
    ],
    "RA": [
        ("MC23112", "Environmental Science and Engineering", "Mandatory"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Mandatory"),
        ("GE23217", "Heritage of Tamils and Technology", "Mandatory"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("RO23523", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("RO23722", "Project Work- Phase I", "EEC"),
        ("RO23821", "Project Work- Phase II", "EEC"),
    ],
    "CSE-CS": [
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("CS23421", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("CR23721", "Project Phase I", "EEC"),
        ("CR23821", "Project Phase II", "EEC"),
    ],
    "FT": [
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("FT23711", "Problem Solving using AI-ML for Food Technologists", "EEC"),
        ("FT23712", "Internship", "EEC"),
        ("FT23811", "Project Work", "EEC"),
    ],
    "IT": [
        ("MC23112", "Environmental Science and Engineering", "Non-credit"),
        ("MC23111", "Indian Constitution and Freedom Movement", "Non-credit"),
        ("GE23421", "Soft Skills-I", "EEC"),
        ("IT23421", "Internship", "EEC"),
        ("GE23521", "Soft Skills-II", "EEC"),
        ("GE23627", "Design Thinking and Innovation", "EEC"),
        ("GE23621", "Problem Solving Techniques", "EEC"),
        ("IT23722", "Project Phase I", "EEC"),
        ("IT23821", "Project Phase II", "EEC"),
    ],
}


def subject_count(code: str) -> int:
    return sum(len(sem["subjects"]) for sem in CURRICULA[code].values())


SUBJECT_COUNTS = {code: subject_count(code) for code in CURRICULA}
