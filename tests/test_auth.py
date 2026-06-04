from src.common.auth.jwt import create_token, decode_token
from src.common.auth.password import hash_password, verify_password


def test_jwt_create_and_decode():
    token = create_token("user-123", {"role": "admin"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"


def test_jwt_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None


def test_password_hash_and_verify():
    hashed = hash_password("my-secret-password")
    assert hashed != "my-secret-password"
    assert verify_password("my-secret-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_password_hash_is_different_each_time():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2
