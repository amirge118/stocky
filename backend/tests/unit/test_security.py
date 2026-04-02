"""Unit tests for app/core/security.py."""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

# ── password hashing ─────────────────────────────────────────────────────────


def test_get_password_hash_returns_non_plaintext():
    hashed = get_password_hash("mysecret")
    assert isinstance(hashed, str)
    assert hashed != "mysecret"


def test_verify_password_correct_returns_true():
    hashed = get_password_hash("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_wrong_returns_false():
    hashed = get_password_hash("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_password_over_72_utf8_bytes_hashes_and_verifies():
    """bcrypt 4+ rejects >72 UTF-8 bytes; we truncate consistently on hash and verify."""
    # 50 × 2-byte UTF-8 chars → 100 bytes (exceeds bcrypt limit)
    pw = "й" * 50
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed) is True


# ── JWT creation ──────────────────────────────────────────────────────────────


def test_create_access_token_returns_non_empty_string():
    token = create_access_token({"sub": "user@example.com"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_returns_payload():
    data = {"sub": "user@example.com", "role": "admin"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user@example.com"
    assert payload["role"] == "admin"


def test_decode_access_token_invalid_token_returns_none():
    result = decode_access_token("this.is.garbage")
    assert result is None


def test_create_access_token_with_explicit_expires_delta_has_exp():
    token = create_access_token(
        {"sub": "tester"}, expires_delta=timedelta(minutes=15)
    )
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload
