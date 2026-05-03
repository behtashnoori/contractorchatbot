"""Invoice RBAC: contractor scope vs staff-wide access (PostgreSQL via TEST_DATABASE_URL)."""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest

from app.extensions import db
from app.models import Contractor, InvoiceSummary, User

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="TEST_DATABASE_URL not set",
)


def _id_suffix() -> str:
    return uuid.uuid4().hex[:12]


def test_contractor_sees_only_own_invoices(client, app_ctx):
    suffix = _id_suffix()
    dc_a = f"ia_{suffix}a"[:32]
    dc_b = f"ia_{suffix}b"[:32]
    cover_a = f"IA-A-{suffix}"
    cover_b = f"IA-B-{suffix}"
    supplier = "99"
    username = f"inv_co_{suffix}"

    with app_ctx.app_context():
        c_a = Contractor(
            detail_code=dc_a,
            supplier_code=supplier,
            name="Inv Test A",
            status="فعال",
            type="test",
        )
        c_b = Contractor(
            detail_code=dc_b,
            supplier_code=supplier,
            name="Inv Test B",
            status="فعال",
            type="test",
        )
        db.session.add_all([c_a, c_b])
        db.session.flush()
        s_a = InvoiceSummary(
            contractor_id=c_a.id,
            detail_code=dc_a,
            supplier_code=supplier,
            cover_number=cover_a,
            invoice_created_at=date(2024, 6, 1),
            invoice_status="pending",
        )
        s_b = InvoiceSummary(
            contractor_id=c_b.id,
            detail_code=dc_b,
            supplier_code=supplier,
            cover_number=cover_b,
            invoice_created_at=date(2024, 6, 2),
            invoice_status="pending",
        )
        db.session.add_all([s_a, s_b])
        user = User(
            username=username,
            contractor_id=c_a.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("inv-co-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "inv-co-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        res = client.get(
            "/invoices/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body.get("total") == 1
        covers = {item["cover_number"] for item in body.get("items", [])}
        assert cover_a in covers
        assert cover_b not in covers
    finally:
        with app_ctx.app_context():
            for cover in (cover_a, cover_b):
                for row in InvoiceSummary.query.filter_by(cover_number=cover).all():
                    db.session.delete(row)
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
            for dc in (dc_a, dc_b):
                c = Contractor.query.filter_by(detail_code=dc).first()
                if c:
                    db.session.delete(c)
            db.session.commit()


def test_contractor_cannot_open_other_contractors_invoice(client, app_ctx):
    suffix = _id_suffix()
    dc_a = f"ib_{suffix}a"[:32]
    dc_b = f"ib_{suffix}b"[:32]
    cover_a = f"IB-A-{suffix}"
    cover_b = f"IB-B-{suffix}"
    supplier = "88"
    username = f"inv_den_{suffix}"

    with app_ctx.app_context():
        c_a = Contractor(
            detail_code=dc_a,
            supplier_code=supplier,
            name="Deny A",
            status="فعال",
            type="test",
        )
        c_b = Contractor(
            detail_code=dc_b,
            supplier_code=supplier,
            name="Deny B",
            status="فعال",
            type="test",
        )
        db.session.add_all([c_a, c_b])
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=c_a.id,
                    detail_code=dc_a,
                    supplier_code=supplier,
                    cover_number=cover_a,
                    invoice_created_at=date(2024, 7, 1),
                    invoice_status="pending",
                ),
                InvoiceSummary(
                    contractor_id=c_b.id,
                    detail_code=dc_b,
                    supplier_code=supplier,
                    cover_number=cover_b,
                    invoice_created_at=date(2024, 7, 2),
                    invoice_status="pending",
                ),
            ]
        )
        user = User(
            username=username,
            contractor_id=c_a.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("inv-deny-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "inv-deny-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        res = client.get(
            f"/invoices/{cover_b}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404
        assert res.get_json().get("error") == "not_found"
    finally:
        with app_ctx.app_context():
            for cover in (cover_a, cover_b):
                for row in InvoiceSummary.query.filter_by(cover_number=cover).all():
                    db.session.delete(row)
            u = User.query.filter_by(username=username).first()
            if u:
                db.session.delete(u)
            for dc in (dc_a, dc_b):
                c = Contractor.query.filter_by(detail_code=dc).first()
                if c:
                    db.session.delete(c)
            db.session.commit()


def test_staff_sees_all_invoices(client, app_ctx):
    suffix = _id_suffix()
    dc_a = f"ic_{suffix}a"[:32]
    dc_b = f"ic_{suffix}b"[:32]
    cover_a = f"IC-A-{suffix}"
    cover_b = f"IC-B-{suffix}"
    supplier = "77"
    staff_user = f"inv_staff_{suffix}"

    with app_ctx.app_context():
        c_a = Contractor(
            detail_code=dc_a,
            supplier_code=supplier,
            name="Staff Scope A",
            status="فعال",
            type="test",
        )
        c_b = Contractor(
            detail_code=dc_b,
            supplier_code=supplier,
            name="Staff Scope B",
            status="فعال",
            type="test",
        )
        db.session.add_all([c_a, c_b])
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=c_a.id,
                    detail_code=dc_a,
                    supplier_code=supplier,
                    cover_number=cover_a,
                    invoice_created_at=date(2024, 8, 1),
                    invoice_status="pending",
                ),
                InvoiceSummary(
                    contractor_id=c_b.id,
                    detail_code=dc_b,
                    supplier_code=supplier,
                    cover_number=cover_b,
                    invoice_created_at=date(2024, 8, 2),
                    invoice_status="pending",
                ),
            ]
        )
        user = User(username=staff_user, role="staff", must_change_password=False)
        user.set_password("inv-staff-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": staff_user, "password": "inv-staff-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        for cov in (cover_a, cover_b):
            res = client.get(
                "/invoices/",
                query_string={"cover_number": cov},
                headers=headers,
            )
            assert res.status_code == 200
            body = res.get_json()
            assert body.get("total") == 1
            assert body["items"][0]["cover_number"] == cov
        all_res = client.get("/invoices/", headers=headers)
        assert all_res.status_code == 200
        assert all_res.get_json().get("total", 0) >= 2
    finally:
        with app_ctx.app_context():
            for cover in (cover_a, cover_b):
                for row in InvoiceSummary.query.filter_by(cover_number=cover).all():
                    db.session.delete(row)
            u = User.query.filter_by(username=staff_user).first()
            if u:
                db.session.delete(u)
            for dc in (dc_a, dc_b):
                c = Contractor.query.filter_by(detail_code=dc).first()
                if c:
                    db.session.delete(c)
            db.session.commit()
