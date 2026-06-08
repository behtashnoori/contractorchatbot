"""Security-focused auth tests (PostgreSQL via TEST_DATABASE_URL)."""

from __future__ import annotations

import os
import uuid

import pytest

from app.extensions import db
from app.models import Contractor, User

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="TEST_DATABASE_URL not set; see docs/TEST_DATABASE_SETUP.md",
)


def _id_suffix() -> str:
    return uuid.uuid4().hex[:12]


def test_login_success(client, app_ctx):
    username = f"pt_ok_{_id_suffix()}"
    with app_ctx.app_context():
        user = User(username=username, role="staff", must_change_password=False)
        user.set_password("correct-horse-battery-12")
        db.session.add(user)
        db.session.commit()

    try:
        res = client.post(
            "/auth/login",
            json={"username": username, "password": "correct-horse-battery-12"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body.get("access_token")
        assert body.get("refresh_token")
    finally:
        with app_ctx.app_context():
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
                db.session.commit()


def test_login_failure_wrong_password(client, app_ctx):
    username = f"pt_fail_{_id_suffix()}"
    with app_ctx.app_context():
        user = User(username=username, role="staff", must_change_password=False)
        user.set_password("right-password-99")
        db.session.add(user)
        db.session.commit()

    try:
        res = client.post(
            "/auth/login",
            json={"username": username, "password": "wrong-password-00"},
        )
        assert res.status_code == 401
        assert res.get_json().get("error") == "invalid_credentials"
    finally:
        with app_ctx.app_context():
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
                db.session.commit()


def test_rbac_contractor_cannot_access_staff_upload(client, app_ctx):
    """Contractor JWT must not pass staff gate on /admin/uploads."""
    username = f"pt_co_{_id_suffix()}"
    dc = f"ptdc{_id_suffix()}"
    with app_ctx.app_context():
        c = Contractor(
            detail_code=dc,
            supplier_code="99",
            name="Pytest Co",
            status="فعال",
            type="test",
        )
        db.session.add(c)
        db.session.flush()
        user = User(
            username=username,
            contractor_id=c.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("contractor-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "contractor-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        res = client.post(
            "/admin/uploads",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert res.get_json().get("error") == "forbidden"
    finally:
        with app_ctx.app_context():
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
            c_obj = Contractor.query.filter_by(detail_code=dc).first()
            if c_obj:
                db.session.delete(c_obj)
            db.session.commit()


def test_rbac_staff_can_reach_upload_validation(client, app_ctx):
    """Staff user passes RBAC; endpoint returns no_files without multipart body."""
    username = f"pt_st_{_id_suffix()}"
    with app_ctx.app_context():
        user = User(username=username, role="staff", must_change_password=False)
        user.set_password("staff-passphrase-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "staff-passphrase-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        res = client.post(
            "/admin/uploads",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert res.get_json().get("error") == "no_files"
    finally:
        with app_ctx.app_context():
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
                db.session.commit()


def test_role_change_affects_next_request_without_new_login(client, app):
    """Authorization uses DB role; same access token works after role promotion/demotion."""
    username = f"pt_role_{_id_suffix()}"
    dc = f"ptdc{_id_suffix()}"
    with app.app_context():
        c = Contractor(
            detail_code=dc,
            supplier_code="88",
            name="Pytest Role",
            status="فعال",
            type="test",
        )
        db.session.add(c)
        db.session.flush()
        user = User(
            username=username,
            contractor_id=c.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("role-test-pass-12")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "role-test-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        blocked = client.post("/admin/uploads", headers=headers)
        assert blocked.status_code == 403

        with app.app_context():
            assert User.query.filter_by(username=username).update({"role": "staff"}) == 1
            db.session.commit()
            assert User.query.filter_by(username=username).first().role == "staff"
            db.session.remove()

        promoted = client.post("/admin/uploads", headers=headers)
        assert promoted.status_code == 400
        assert promoted.get_json().get("error") == "no_files"

        with app.app_context():
            assert User.query.filter_by(username=username).update({"role": "contractor"}) == 1
            db.session.commit()
            assert User.query.filter_by(username=username).first().role == "contractor"
            db.session.remove()

        demoted = client.post("/admin/uploads", headers=headers)
        assert demoted.status_code == 403
    finally:
        with app.app_context():
            u = db.session.get(User, user_id)
            if u:
                db.session.delete(u)
            c_obj = Contractor.query.filter_by(detail_code=dc).first()
            if c_obj:
                db.session.delete(c_obj)
            db.session.commit()


def test_deleted_user_token_cannot_access_staff_upload(client, app):
    """A token whose user row was deleted must not authorize admin endpoints."""
    username = f"pt_deleted_{_id_suffix()}"
    with app.app_context():
        user = User(username=username, role="staff", must_change_password=False)
        user.set_password("deleted-user-pass-12")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    login = client.post(
        "/auth/login",
        json={"username": username, "password": "deleted-user-pass-12"},
    )
    assert login.status_code == 200
    token = login.get_json()["access_token"]

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        db.session.delete(user)
        db.session.commit()
        db.session.remove()

    res = client.post(
        "/admin/uploads",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.get_json().get("error") == "not_found"


def test_inactive_contractor_token_cannot_continue_or_refresh(client, app):
    """Existing tokens stop working after the linked contractor is deactivated."""
    username = f"pt_inactive_{_id_suffix()}"
    dc = f"ptinactive{_id_suffix()}"[:32]
    with app.app_context():
        contractor = Contractor(
            detail_code=dc,
            supplier_code="77",
            name="Pytest Inactive",
            status="ظپط¹ط§ظ„",
            type="test",
            is_active=True,
        )
        db.session.add(contractor)
        db.session.flush()
        user = User(
            username=username,
            contractor_id=contractor.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("inactive-token-pass-12")
        db.session.add(user)
        db.session.commit()
        contractor_id = contractor.id

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "inactive-token-pass-12"},
        )
        assert login.status_code == 200
        tokens = login.get_json()

        with app.app_context():
            contractor = db.session.get(Contractor, contractor_id)
            contractor.is_active = False
            db.session.commit()
            db.session.remove()

        access_res = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert access_res.status_code == 403
        assert access_res.get_json().get("error") == "forbidden"

        refresh_res = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert refresh_res.status_code == 403
        assert refresh_res.get_json().get("error") == "forbidden"
    finally:
        with app.app_context():
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
            c = Contractor.query.filter_by(detail_code=dc).first()
            if c:
                db.session.delete(c)
            db.session.commit()
