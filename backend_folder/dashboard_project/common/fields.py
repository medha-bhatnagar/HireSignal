"""
A small, dependency-light encrypted text field.

Rather than pulling in a whole third-party "encrypted model fields" package,
this wraps the standard library-adjacent `cryptography` package (already a
transitive dependency of a lot of the Python ecosystem, and small/well
audited) directly. It's intentionally simple: encrypt on the way into the
database, decrypt on the way out. Django never sees or logs the plaintext
outside of Python memory.

Requires FIELD_ENCRYPTION_KEY in settings -- generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _get_fernet() -> Fernet:
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        raise ValueError(
            "FIELD_ENCRYPTION_KEY is not set. Generate one with:\n"
            "  python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"\n"
            "and put it in your .env as FIELD_ENCRYPTION_KEY=..."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


class EncryptedTextField(models.TextField):
    """
    A TextField that is encrypted in the database and decrypted transparently
    when read back through the ORM. Used for User.github_access_token so a
    leaked database dump doesn't hand out working GitHub credentials.
    """

    def get_prep_value(self, value):
        # Called when Django is about to write the value to the database.
        if value is None or value == "":
            return value
        f = _get_fernet()
        return f.encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        # Called when Django reads the raw column value back from the database.
        if value is None or value == "":
            return value
        f = _get_fernet()
        try:
            return f.decrypt(value.encode()).decode()
        except InvalidToken:
            # Value was stored before encryption was added, or the key
            # rotated -- fail closed rather than returning garbage.
            return None
