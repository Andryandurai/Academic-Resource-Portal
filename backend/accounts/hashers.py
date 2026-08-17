"""Compatibility hasher for accounts carried over from the previous stack.

The Next.js implementation hashed passwords with `bcryptjs`, producing a bare
modular-crypt string (`$2a$12$...`). Django stores an algorithm prefix, so the
migration writes those as `bcrypt$$2a$12$...` and this hasher reads them.

It exists purely so nobody has to reset their password because the backend
changed language. It is *not* the hasher for new passwords — PBKDF2 is listed
first in PASSWORD_HASHERS, and Django re-hashes a legacy password to PBKDF2 on
the owner's next successful login.
"""

from __future__ import annotations

from django.contrib.auth.hashers import BCryptPasswordHasher


class LegacyBCryptPasswordHasher(BCryptPasswordHasher):
    """bcrypt as written by bcryptjs, including the `$2a$` variant marker."""

    algorithm = "bcrypt"
    library = ("bcrypt", "bcrypt")
