"""One-off: publish the admin's own AI&DS study files as Resources.

Reads backend's sibling `studies/` folder (one subfolder per subject, named
however the admin happened to name it) and files each document under the real
AI&DS subject and unit its name or folder implies. Not a general-purpose
importer — the mapping below is specific to this one folder tree, built by
inspecting every filename once; run it again and it only fills in gaps, since
each file is looked up by subject+unit+title before being created.
"""

from __future__ import annotations

from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from academics.models import Department, Subject
from core.validators import extension_of, sanitize_display_name
from resources.models import ContentKind, Resource, ResourceType

# folder name -> (semester_number, course_code)
FOLDER_SUBJECT: dict[str, tuple[int, str]] = {
    "beee": (1, "EE23133"),
    "Physics": (1, "PH23132"),
    "Programming using C": (1, "GE23131"),
    "Heritage of Tamils": (1, "GE23117"),
    "math": (1, "MA23116"),
    "data structures": (2, "CS23231"),
    "dpca": (2, "IT23231"),
    "eg": (2, "GE23111"),
    "poai": (2, "AI23231"),
    "math 2": (2, "MA23214"),
    "daa": (3, "CS23331"),
    "dbms": (3, "CS23332"),
    "foml": (3, "AI23331"),
    "Big-data": (5, "AD23531"),
    "Computer Networks": (5, "CS23532"),
}

# Folders with no confident match in the AI&DS curriculum — reported, not
# guessed. "icfm" (MC23111) isn't part of AI&DS's own course list at all;
# "pis" and "PODS" don't correspond to any AI&DS title; "python" is one
# practice .py file, not a document format this portal publishes.
UNMAPPED_FOLDERS = {"icfm", "pis", "PODS", "python"}

# file (relative to its subject folder, forward slashes) -> ResourceType.
# Anything not listed here falls back to UNIT_1 — a deliberate, reported
# default for a file whose name gives no unit at all, rather than skipping
# real material the admin asked to have published.
FILE_UNIT: dict[str, str] = {
    # beee — four parts of the same unit, all kept as separate resources
    "BEEE Unit 2 notes.pdf": ResourceType.UNIT_2,
    "BEEE unit 4 notes.pdf": ResourceType.UNIT_4,
    "BEEE unit 5 notes.pdf": ResourceType.UNIT_5,
    "Beee Unit -3 part 1.pdf": ResourceType.UNIT_3,
    "Beee notes Unit -3 Part-4.pdf": ResourceType.UNIT_3,
    "Beee notes Unit-3 Part 2.pdf": ResourceType.UNIT_3,
    "Beee notes Unit-3 Part 3.pdf": ResourceType.UNIT_3,
    # Physics
    "unit 4.pdf": ResourceType.UNIT_4,
    # data structures
    "u1.pdf": ResourceType.UNIT_1,
    "u2.pdf": ResourceType.UNIT_2,
    "u3.pdf": ResourceType.UNIT_3,
    "u4.pdf": ResourceType.UNIT_4,
    "u5.pdf": ResourceType.UNIT_5,
    # dpca
    "4.pdf": ResourceType.UNIT_4,
    "DPCA UNIT 4 extra.pdf": ResourceType.UNIT_4,
    "IT 23231 DPCA UNIT 05- FIRST HALF.pdf": ResourceType.UNIT_5,
    "IT 23231 DPCA UNIT 05-SECOND HALF.pdf": ResourceType.UNIT_5,
    "u1 pdf.pdf": ResourceType.UNIT_1,
    "u2 ppt.ppt": ResourceType.UNIT_2,
    "u2 ppt2.pptx": ResourceType.UNIT_2,
    "u3 ppt.pptx": ResourceType.UNIT_3,
    "unit 2.pdf": ResourceType.UNIT_2,
    "unit 3.pdf": ResourceType.UNIT_3,
    "unit 4.pdf": ResourceType.UNIT_4,
    # eg — "2nd half" is sections of solids, the topic that follows Unit 3's
    # projection-of-solids (checked one photo: a hexagonal-prism section
    # problem), which this syllabus files under Unit 4.
    "unit I.pptx": ResourceType.UNIT_1,
    "Projection of point and line.pptx": ResourceType.UNIT_2,
    "Projection of planes.pdf": ResourceType.UNIT_2,
    "Projection of planes.pptx": ResourceType.UNIT_2,
    "Projection of solid.pptx": ResourceType.UNIT_3,
    **{f"2nd half/{n}": ResourceType.UNIT_4 for n in [
        "IMG-20250604-WA0020.jpg", "IMG-20250604-WA0021.jpg", "IMG-20250604-WA0022.jpg",
        "IMG-20250604-WA0023.jpg", "IMG-20250604-WA0024.jpg", "IMG-20250604-WA0025.jpg",
        "IMG-20250604-WA0026.jpg", "IMG-20250604-WA0027.jpg", "IMG-20250604-WA0028.jpg",
        "IMG-20250604-WA0029.jpg", "IMG-20250604-WA0030.jpg", "IMG-20250604-WA0031.jpg",
        "IMG-20250604-WA0032.jpg", "IMG-20250604-WA0033.jpg", "IMG-20250604-WA0034.jpg",
        "IMG-20250604-WA0035.jpg",
    ]},
    # dbms / daa / Computer Networks / Big-data — explicit already
    "UNIT I  PPT .pdf": ResourceType.UNIT_1,
    "DAA Unit-1.pdf": ResourceType.UNIT_1,
    "Unit I.pdf": ResourceType.UNIT_1,
    "BDA Unit 1 Material.pdf": ResourceType.UNIT_1,
    "BDA Unit 2 Material.pdf": ResourceType.UNIT_2,
    "BDA Unit 3 Material.pdf": ResourceType.UNIT_3,
    # math / math 2
    "UNIT I MCQS.pdf": ResourceType.UNIT_1,
    "UNIT I- Part B.pdf": ResourceType.UNIT_1,
    "UNIT I-Continuation.pdf": ResourceType.UNIT_1,
    "UNIT I.pdf": ResourceType.UNIT_1,
    "ch 1.pdf": ResourceType.UNIT_1,
    # poai
    "notes_aids.pdf": ResourceType.UNIT_1,
    # Heritage of Tamils
    "Heritage-of-Tamils-English-Lectures-(upto Unit I).pdf": ResourceType.UNIT_1,
}

# Files not worth publishing as unit material at all.
SKIP_FILES = {"Heritage of Tamils/syllabus.pdf"}

# foml's one file covers two units at once — published under both rather
# than picked for just one, since its own filename claims both.
DUAL_UNIT: dict[str, list[str]] = {
    "foml/u1,2.pdf": [ResourceType.UNIT_1, ResourceType.UNIT_2],
}


class Command(BaseCommand):
    help = "Publish backend/../studies/ files as AI&DS Resources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--studies-dir",
            default=None,
            help="Defaults to <repo root>/studies",
        )
        parser.add_argument("--uploaded-by", default=None, help="Admin email to credit as uploader.")

    def handle(self, *args, **options):
        from django.conf import settings

        studies_dir = Path(options["studies_dir"] or (settings.REPO_ROOT / "studies"))
        if not studies_dir.is_dir():
            self.stderr.write(f"No such directory: {studies_dir}")
            return

        department = Department.objects.get(code="AI&DS")
        uploader = None
        if options["uploaded_by"]:
            from accounts.models import User

            uploader = User.objects.filter(email=options["uploaded_by"]).first()

        created, skipped, unmapped, too_large = 0, 0, [], []

        for folder in sorted(p for p in studies_dir.iterdir() if p.is_dir()):
            name = folder.name
            if name in UNMAPPED_FOLDERS:
                unmapped.append(name)
                continue
            mapping = FOLDER_SUBJECT.get(name)
            if not mapping:
                unmapped.append(name)
                continue

            semester_number, course_code = mapping
            subject = Subject.objects.filter(
                semester__department=department,
                semester__semester_number=semester_number,
                course_code=course_code,
            ).first()
            if not subject:
                self.stderr.write(f"No subject {course_code} in semester {semester_number} — skipping {name}")
                continue

            for file_path in sorted(folder.rglob("*")):
                if not file_path.is_file():
                    continue
                rel = file_path.relative_to(folder).as_posix()
                skip_key = f"{name}/{rel}"
                if skip_key in SKIP_FILES:
                    skipped += 1
                    continue

                if file_path.stat().st_size > settings.MAX_UPLOAD_BYTES:
                    too_large.append(f"{skip_key} ({file_path.stat().st_size / 1024 / 1024:.0f} MB)")
                    continue

                dual_key = f"{name}/{rel}"
                unit_choices = DUAL_UNIT.get(dual_key) or [FILE_UNIT.get(rel, ResourceType.UNIT_1)]

                for unit in unit_choices:
                    title = file_path.stem.strip() or file_path.name
                    if Resource.objects.filter(
                        subject=subject, resource_type=unit, title=title, kind=ContentKind.NOTES
                    ).exists():
                        continue  # already published — safe to re-run this command

                    ext = extension_of(file_path.name)
                    with file_path.open("rb") as fh:
                        resource = Resource(
                            subject=subject,
                            resource_type=unit,
                            kind=ContentKind.NOTES,
                            title=title,
                            description="",
                            file_name=sanitize_display_name(file_path.name),
                            file_ext=ext,
                            file_type=_media_type_for(ext),
                            file_size=file_path.stat().st_size,
                            uploaded_by=uploader,
                        )
                        resource.file.save(file_path.name, File(fh), save=True)
                    created += 1
                    self.stdout.write(f"  + [{course_code} {unit}] {title}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Created {created} resources, skipped {skipped}."))
        if unmapped:
            self.stdout.write(
                self.style.WARNING(
                    "Folders not published (no confident subject match): " + ", ".join(sorted(set(unmapped)))
                )
            )
        if too_large:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped (over the {settings.MAX_UPLOAD_MB:g} MB limit): " + ", ".join(too_large)
                )
            )


def _media_type_for(ext: str) -> str:
    from core.validators import FORMATS_BY_EXT

    fmt = FORMATS_BY_EXT.get(ext)
    return fmt.media_types[0] if fmt else "application/octet-stream"
