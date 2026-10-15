"""Staff authentication primitives: Argon2 password hashing and signed session tokens (SPEC 7.4)."""

from datetime import timedelta

from itsdangerous import BadSignature, URLSafeTimedSerializer
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher
from pydantic import SecretStr

SESSION_COOKIE = "bs_session"
SESSION_MAX_AGE = timedelta(hours=12)
_SESSION_SALT = "bright-smile.staff-session"
_SESSION_SUBJECT = "staff"

_hasher = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time check. CPU-bound: call it from a thread pool in request handlers."""
    try:
        return _hasher.verify(password, password_hash)
    except UnknownHashError:
        return False


class SessionSigner:
    """Issues and verifies tamper-proof, expiring staff session tokens."""

    def __init__(self, secret: SecretStr, max_age: timedelta = SESSION_MAX_AGE) -> None:
        self._serializer = URLSafeTimedSerializer(secret.get_secret_value(), salt=_SESSION_SALT)
        self._max_age = max_age

    @property
    def max_age(self) -> timedelta:
        return self._max_age

    def issue(self) -> str:
        return self._serializer.dumps({"sub": _SESSION_SUBJECT})

    def verify(self, token: str) -> bool:
        try:
            payload = self._serializer.loads(token, max_age=int(self._max_age.total_seconds()))
        except BadSignature:  # also covers SignatureExpired
            return False
        return isinstance(payload, dict) and payload.get("sub") == _SESSION_SUBJECT
