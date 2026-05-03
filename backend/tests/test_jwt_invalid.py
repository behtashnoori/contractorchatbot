"""JWT validation tests that do not require a live database."""

# Well-formed HS256 JWT (sample payload) whose signature does not match pytest JWT_SECRET_KEY.
_BAD_SIG_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)


def test_invalid_jwt_rejected_on_me(client_jwt_only):
    res = client_jwt_only.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_BAD_SIG_JWT}"},
    )
    assert res.status_code == 401
    assert res.get_json().get("error") == "invalid_token"
