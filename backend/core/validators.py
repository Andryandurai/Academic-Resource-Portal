"""Upload validation.

Three independent checks have to agree before a file is accepted: the extension,
the media type the browser declared, and the file's own signature. The signature
check is the one that matters — extension and content type are both attacker
controlled, so a renamed executable passes the first two and fails only here.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


@dataclass(frozen=True)
class FileFormat:
    ext: str
    label: str
    media_types: tuple[str, ...]
    inline_viewable: bool


# PDF first: it is the primary academic format and the only one previewed in the
# browser. Everything else is offered as a download.
ALLOWED_FORMATS: tuple[FileFormat, ...] = (
    FileFormat("pdf", "PDF", ("application/pdf",), True),
    FileFormat("doc", "Word 97-2003", ("application/msword",), False),
    FileFormat(
        "docx",
        "Word",
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document",),
        False,
    ),
    FileFormat("ppt", "PowerPoint 97-2003", ("application/vnd.ms-powerpoint",), False),
    FileFormat(
        "pptx",
        "PowerPoint",
        ("application/vnd.openxmlformats-officedocument.presentationml.presentation",),
        False,
    ),
    FileFormat("xls", "Excel 97-2003", ("application/vnd.ms-excel",), False),
    FileFormat(
        "xlsx",
        "Excel",
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",),
        False,
    ),
    # A phone photo of a handwritten or printed page — the everyday form
    # scanned notes actually arrive in, alongside the scanned-to-PDF form.
    FileFormat("jpg", "JPEG Image", ("image/jpeg",), True),
    FileFormat("jpeg", "JPEG Image", ("image/jpeg",), True),
    FileFormat("png", "PNG Image", ("image/png",), True),
)

FORMATS_BY_EXT = {fmt.ext: fmt for fmt in ALLOWED_FORMATS}
ALLOWED_EXTENSIONS = tuple(FORMATS_BY_EXT)

# Office 2007+ formats are ZIP containers; the pre-2007 formats are OLE compound
# files. Neither signature identifies the specific application, which is the
# honest limit of a magic-byte check — it rules out executables and scripts, not
# a .docx renamed to .xlsx.
_PDF_MAGIC = b"%PDF-"
_ZIP_MAGIC = b"PK"
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_OOXML = {"docx", "pptx", "xlsx"}
_LEGACY_OFFICE = {"doc", "ppt", "xls"}
_JPEG = {"jpg", "jpeg"}

_ILLEGAL_NAME_CHARS = re.compile(r'[\x00-\x1f\x7f<>:"|?*\\/]')


def file_type_label(ext: str) -> str:
    fmt = FORMATS_BY_EXT.get((ext or "").lower())
    return fmt.label if fmt else (ext or "").upper()


def is_inline_viewable(ext: str) -> bool:
    fmt = FORMATS_BY_EXT.get((ext or "").lower())
    return bool(fmt and fmt.inline_viewable)


def extension_of(filename: str) -> str:
    match = re.search(r"\.([A-Za-z0-9]+)$", filename or "")
    return match.group(1).lower() if match else ""


def sanitize_display_name(filename: str) -> str:
    """Strip directory components and characters that are illegal in a path.

    The result is stored for display only — it is never used to build the path
    a file is written to — but keeping it clean avoids surprises if an operator
    re-saves it locally.
    """
    base = (filename or "").replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFC", base)
    cleaned = _ILLEGAL_NAME_CHARS.sub("", base).strip()
    return (cleaned or "file")[:200]


def storage_filename(ext: str) -> str:
    """An opaque, server-generated name. No user input reaches the filesystem."""
    return f"{uuid.uuid4().hex}.{ext}"


def _read_signature(upload: UploadedFile, length: int = 1024) -> bytes:
    position = upload.tell()
    try:
        upload.seek(0)
        head = upload.read(length)
    finally:
        # The serializer and the storage backend both read the file afterwards;
        # leaving the cursor moved would truncate whatever is saved.
        upload.seek(position)
    return head or b""


def _signature_matches(head: bytes, ext: str) -> bool:
    if ext == "pdf":
        # Some producers emit whitespace or a BOM before the header.
        return _PDF_MAGIC in head[:1024]
    if ext in _OOXML:
        return head[:2] == _ZIP_MAGIC
    if ext in _LEGACY_OFFICE:
        return head[:8] == _OLE_MAGIC
    if ext in _JPEG:
        return head[:3] == _JPEG_MAGIC
    if ext == "png":
        return head[:8] == _PNG_MAGIC
    return False


def validate_upload(upload: UploadedFile) -> tuple[str, str]:
    """Validate an uploaded file. Returns ``(extension, media_type)``.

    Raises ``ValidationError`` with a message written for the administrator
    doing the upload rather than for a log file.
    """
    if upload is None or not getattr(upload, "size", 0):
        raise ValidationError("Select a file to upload.")

    max_bytes = settings.MAX_UPLOAD_BYTES
    if upload.size > max_bytes:
        raise ValidationError(
            f"File is too large. The maximum upload size is {settings.MAX_UPLOAD_MB:g} MB."
        )

    display_name = sanitize_display_name(upload.name)
    ext = extension_of(display_name)

    if not ext:
        raise ValidationError("The file must have an extension.")
    if ext not in FORMATS_BY_EXT:
        allowed = ", ".join(e.upper() for e in ALLOWED_EXTENSIONS)
        raise ValidationError(
            f'Unsupported file type ".{ext}". Allowed formats: {allowed}.'
        )

    fmt = FORMATS_BY_EXT[ext]
    declared = (getattr(upload, "content_type", "") or "").split(";")[0].strip().lower()
    # An empty or generic type is common on some platforms, and the signature
    # check below is the authoritative test — so only a *contradicting* type is
    # rejected here.
    if declared and declared not in ("application/octet-stream",) and declared not in fmt.media_types:
        raise ValidationError(
            f'The declared content type "{declared}" does not match a .{ext} document.'
        )

    if not _signature_matches(_read_signature(upload), ext):
        raise ValidationError(
            f"This file does not appear to be a valid {ext.upper()} document. "
            "Upload the original file rather than a renamed one."
        )

    return ext, fmt.media_types[0]
