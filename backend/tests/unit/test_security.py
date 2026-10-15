import time
from datetime import timedelta

import pytest
from itsdangerous import TimestampSigner
from pydantic import SecretStr

from bright_smile.core.security import SessionSigner, hash_password, verify_password


def test_password_hash_round_trip() -> None:
    hashed = hash_password("correct horse battery staple")

    assert hashed.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong", hashed)


def test_malformed_hash_never_verifies() -> None:
    assert verify_password("anything", "not-a-hash") is False


def test_session_tokens_verify_and_reject_tampering() -> None:
    signer = SessionSigner(SecretStr("s" * 32))
    token = signer.issue()

    assert signer.verify(token)
    assert not signer.verify(token[:-2] + "xx")
    assert not SessionSigner(SecretStr("other-secret-" * 3)).verify(token)


def test_session_tokens_expire(monkeypatch: pytest.MonkeyPatch) -> None:
    signer = SessionSigner(SecretStr("s" * 32), max_age=timedelta(seconds=60))
    token = signer.issue()
    issued_at = int(time.time())

    monkeypatch.setattr(TimestampSigner, "get_timestamp", lambda _self: issued_at + 61)

    assert not signer.verify(token)
