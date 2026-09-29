"""One-time migration: copy existing local resource files into Supabase
Storage (or any S3-compatible bucket configured via REC_S3_*), without
changing a single Resource row.

    python manage.py migrate_resources_to_storage --dry-run
    python manage.py migrate_resources_to_storage --migrate
    python manage.py migrate_resources_to_storage --verify

Why no database write is needed
--------------------------------
`resource_upload_path()` (resources/models.py) already names every file
`resources/subject-<id>/<uuid>.<ext>` and `Resource.file` stores exactly that
relative path, never an absolute one. Django's storage abstraction resolves
that same relative path against whichever backend `STORAGES["default"]`
currently points at (`FileSystemStorage` today, `S3Storage` once
`REC_S3_ACCESS_KEY_ID` is set — see settings.py). So migrating storage is
purely a matter of making sure every key that exists on local disk also
exists, byte-for-byte, in the bucket under the identical key. Nothing in
`Resource` needs to change, and nothing does — this command never writes to
the database.

Source and destination are constructed explicitly (not via `default_storage`)
so this command behaves the same regardless of which backend is currently
configured as default: local disk is always the source, the S3-compatible
bucket is always the destination.

Safety
------
- Never deletes a local file.
- Never overwrites a remote object that doesn't already match by size
  (reports a CONFLICT and stops for that resource instead).
- Never touches Resource, Department, Semester, Subject or User rows.
- `--dry-run` (the default when no mode is given) makes no network calls
  that write anything and uploads nothing.
"""

from __future__ import annotations

import hashlib
import os

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError

from resources.models import ContentKind, Resource

CHUNK = 65536


def _sha256_of(fh) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: fh.read(CHUNK), b""):
        h.update(chunk)
    return h.hexdigest()


class Command(BaseCommand):
    help = "Copy existing local resource files into the configured S3-compatible bucket."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would happen. Uploads nothing. Default if no mode is given.",
        )
        mode.add_argument(
            "--migrate",
            action="store_true",
            help="Upload any resource file not yet present in the bucket.",
        )
        mode.add_argument(
            "--verify",
            action="store_true",
            help=(
                "For every resource already present remotely, download it back and "
                "compare its SHA-256 against the local file. Read-only; uploads nothing."
            ),
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"] or not (options["migrate"] or options["verify"])
        do_migrate = options["migrate"]
        do_verify = options["verify"]

        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)

        remote_storage = self._remote_storage()
        if remote_storage is None:
            self.stdout.write(
                self.style.WARNING(
                    "REC_S3_ACCESS_KEY_ID is not set — no S3-compatible storage is "
                    "configured. Showing the local inventory only; nothing can be "
                    "checked or uploaded remotely until Supabase Storage credentials "
                    "are added to backend/.env (see docs/SUPABASE_SETUP.md)."
                )
            )

        resources = Resource.objects.filter(kind=ContentKind.NOTES).order_by("id")
        total = resources.count()
        self.stdout.write(f"{total} file-backed resource(s) found.\n")

        counts = {"already_migrated": 0, "uploaded": 0, "would_upload": 0, "local_only": 0, "failed": 0}

        for resource in resources:
            key = resource.file.name
            status = self._handle_one(
                resource, key, local_storage, remote_storage, dry_run, do_migrate, do_verify
            )
            counts[status] = counts.get(status, 0) + 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Done. {total} resource(s) checked."))
        for label, n in counts.items():
            if n:
                self.stdout.write(f"  {label.replace('_', ' ')}: {n}")

        if counts["failed"]:
            raise CommandError(
                f"{counts['failed']} resource(s) failed or conflicted — see PASS/FAIL lines above. "
                "No local file was touched; no remote object was overwritten."
            )

    def _remote_storage(self):
        """The destination bucket, built explicitly from REC_S3_* — never from
        `default_storage`, so this command's behaviour doesn't depend on
        whichever backend STORAGES["default"] currently resolves to."""
        access_key = os.environ.get("REC_S3_ACCESS_KEY_ID", "")
        if not access_key:
            return None
        try:
            from storages.backends.s3 import S3Storage
        except ImportError as exc:  # pragma: no cover - requirements.txt already lists it
            raise CommandError(
                "REC_S3_ACCESS_KEY_ID is set but the 'django-storages' package is not "
                "importable. Run: pip install -r requirements.txt"
            ) from exc

        from boto3.s3.transfer import TransferConfig

        return S3Storage(
            access_key=access_key,
            secret_key=os.environ.get("REC_S3_SECRET_ACCESS_KEY", ""),
            bucket_name=os.environ.get("REC_S3_BUCKET_NAME", "academic-resources"),
            endpoint_url=os.environ.get("REC_S3_ENDPOINT_URL", ""),
            region_name=os.environ.get("REC_S3_REGION_NAME", "us-east-1"),
            addressing_style="path",
            default_acl=None,
            querystring_auth=False,
            file_overwrite=True,
            # Same reasoning as settings.py: Supabase Storage's S3 layer doesn't
            # implement multipart upload, so force a single PUT.
            transfer_config=TransferConfig(multipart_threshold=200 * 1024 * 1024),
        )

    def _handle_one(self, resource, key, local_storage, remote_storage, dry_run, do_migrate, do_verify):
        label = f"id={resource.id:>4}  {key}"

        if not local_storage.exists(key):
            self.stdout.write(self.style.ERROR(f"{label}  FAIL  local file missing"))
            return "failed"

        local_size = local_storage.size(key)
        with local_storage.open(key, "rb") as fh:
            local_hash = _sha256_of(fh)

        if remote_storage is None:
            self.stdout.write(
                f"{label}  size={local_size:>9}  sha256={local_hash[:12]}...  "
                f"LOCAL ONLY (no bucket configured)"
            )
            return "local_only"

        exists_remotely = remote_storage.exists(key)

        if not exists_remotely:
            if dry_run:
                self.stdout.write(f"{label}  size={local_size:>9}  WOULD UPLOAD (dry run)")
                return "would_upload"
            if not do_migrate:
                self.stdout.write(f"{label}  NOT MIGRATED (re-run with --migrate to upload)")
                return "would_upload"

            with local_storage.open(key, "rb") as fh:
                remote_storage.save(key, File(fh))

            if not remote_storage.exists(key):
                self.stdout.write(self.style.ERROR(f"{label}  FAIL  upload did not appear in bucket"))
                return "failed"
            remote_size = remote_storage.size(key)
            if remote_size != local_size:
                self.stdout.write(
                    self.style.ERROR(
                        f"{label}  FAIL  uploaded but size mismatch (local={local_size} remote={remote_size})"
                    )
                )
                return "failed"

            with remote_storage.open(key, "rb") as fh:
                remote_hash = _sha256_of(fh)
            if remote_hash != local_hash:
                self.stdout.write(self.style.ERROR(f"{label}  FAIL  uploaded but content hash mismatch"))
                return "failed"

            self.stdout.write(self.style.SUCCESS(f"{label}  size={local_size:>9}  PASS  uploaded and verified"))
            return "uploaded"

        # Already present remotely.
        remote_size = remote_storage.size(key)
        if remote_size != local_size:
            self.stdout.write(
                self.style.ERROR(
                    f"{label}  CONFLICT  a different object already exists at this key "
                    f"(local={local_size} bytes, remote={remote_size} bytes) — not overwritten"
                )
            )
            return "failed"

        if do_verify:
            with remote_storage.open(key, "rb") as fh:
                remote_hash = _sha256_of(fh)
            if remote_hash != local_hash:
                self.stdout.write(
                    self.style.ERROR(f"{label}  CONFLICT  size matches but content hash differs")
                )
                return "failed"
            self.stdout.write(self.style.SUCCESS(f"{label}  size={local_size:>9}  PASS  verified (hash match)"))
        else:
            self.stdout.write(f"{label}  size={local_size:>9}  already migrated (size match)")

        return "already_migrated"
