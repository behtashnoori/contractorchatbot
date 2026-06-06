"""Invoice RBAC: contractor scope vs staff-wide access (PostgreSQL via TEST_DATABASE_URL)."""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest

from app.extensions import db
from app.models import Contractor, InvoiceDetail, InvoiceSummary, User

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="TEST_DATABASE_URL not set; see docs/TEST_DATABASE_SETUP.md",
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


def test_invoice_endpoints_show_only_active_batch_rows(client, app_ctx):
    suffix = _id_suffix()
    dc = f"ie_{suffix}"[:32]
    inactive_cover = f"IE-OLD-{suffix}"
    active_cover = f"IE-NEW-{suffix}"
    contractor_user = f"inv_active_{suffix}"
    staff_user = f"staff_active_{suffix}"

    with app_ctx.app_context():
        contractor = Contractor(
            detail_code=dc,
            supplier_code="55",
            name="Active Batch Contractor",
            status="فعال",
            type="test",
        )
        db.session.add(contractor)
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=dc,
                    supplier_code="55",
                    cover_number=inactive_cover,
                    invoice_created_at=date(2024, 10, 1),
                    invoice_status="old-active-test",
                    is_active=False,
                ),
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=dc,
                    supplier_code="55",
                    cover_number=active_cover,
                    invoice_created_at=date(2024, 10, 2),
                    invoice_status="new-active-test",
                    is_active=True,
                ),
            ]
        )
        contractor_account = User(
            username=contractor_user,
            contractor_id=contractor.id,
            role="contractor",
            must_change_password=False,
        )
        contractor_account.set_password("active-pass-12")
        staff_account = User(username=staff_user, role="staff", must_change_password=False)
        staff_account.set_password("staff-active-pass-12")
        db.session.add_all([contractor_account, staff_account])
        db.session.commit()

    try:
        contractor_login = client.post(
            "/auth/login",
            json={"username": contractor_user, "password": "active-pass-12"},
        )
        assert contractor_login.status_code == 200
        contractor_token = contractor_login.get_json()["access_token"]
        contractor_res = client.get(
            "/invoices/",
            headers={"Authorization": f"Bearer {contractor_token}"},
        )
        assert contractor_res.status_code == 200
        contractor_covers = {item["cover_number"] for item in contractor_res.get_json()["items"]}
        assert active_cover in contractor_covers
        assert inactive_cover not in contractor_covers

        staff_login = client.post(
            "/auth/login",
            json={"username": staff_user, "password": "staff-active-pass-12"},
        )
        assert staff_login.status_code == 200
        staff_token = staff_login.get_json()["access_token"]
        inactive_detail = client.get(
            f"/invoices/{inactive_cover}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert inactive_detail.status_code == 404
    finally:
        with app_ctx.app_context():
            for cover in (inactive_cover, active_cover):
                for row in InvoiceSummary.query.filter_by(cover_number=cover).all():
                    db.session.delete(row)
            for username in (contractor_user, staff_user):
                user = User.query.filter_by(username=username).first()
                if user:
                    db.session.delete(user)
            contractor = Contractor.query.filter_by(detail_code=dc).first()
            if contractor:
                db.session.delete(contractor)
            db.session.commit()


def test_admin_lists_show_only_active_records_by_default(client, app_ctx):
    suffix = _id_suffix()
    active_dc = f"admin_active_{suffix}"[:32]
    inactive_dc = f"admin_old_{suffix}"[:32]
    active_cover = f"ADM-NEW-{suffix}"
    inactive_cover = f"ADM-OLD-{suffix}"
    active_invoice = f"ADM-D-NEW-{suffix}"
    inactive_invoice = f"ADM-D-OLD-{suffix}"
    staff_user = f"admin_list_{suffix}"

    with app_ctx.app_context():
        active_contractor = Contractor(
            detail_code=active_dc,
            supplier_code="44",
            name=f"Admin Active {suffix}",
            status="فعال",
            type="test",
            is_active=True,
        )
        inactive_contractor = Contractor(
            detail_code=inactive_dc,
            supplier_code="44",
            name=f"Admin Inactive {suffix}",
            status="فعال",
            type="test",
            is_active=False,
        )
        db.session.add_all([active_contractor, inactive_contractor])
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=active_contractor.id,
                    detail_code=active_dc,
                    supplier_code="44",
                    cover_number=active_cover,
                    invoice_created_at=date(2024, 11, 2),
                    invoice_status="admin-active",
                    is_active=True,
                ),
                InvoiceSummary(
                    contractor_id=inactive_contractor.id,
                    detail_code=inactive_dc,
                    supplier_code="44",
                    cover_number=inactive_cover,
                    invoice_created_at=date(2024, 11, 1),
                    invoice_status="admin-inactive",
                    is_active=False,
                ),
                InvoiceDetail(
                    contractor_id=active_contractor.id,
                    detail_code=active_dc,
                    supplier_code="44",
                    cover_number=active_cover,
                    invoice_no=active_invoice,
                    status="active-detail",
                    is_active=True,
                ),
                InvoiceDetail(
                    contractor_id=inactive_contractor.id,
                    detail_code=inactive_dc,
                    supplier_code="44",
                    cover_number=inactive_cover,
                    invoice_no=inactive_invoice,
                    status="inactive-detail",
                    is_active=False,
                ),
            ]
        )
        user = User(username=staff_user, role="staff", must_change_password=False)
        user.set_password("admin-list-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": staff_user, "password": "admin-list-pass-12"},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.get_json()['access_token']}"}

        contractors = client.get(
            "/admin/contractors",
            query_string={"search": suffix},
            headers=headers,
        )
        assert contractors.status_code == 200
        contractor_codes = {item["detail_code"] for item in contractors.get_json()["items"]}
        assert active_dc in contractor_codes
        assert inactive_dc not in contractor_codes

        summaries = client.get(
            "/admin/invoice-summaries",
            query_string={"search": suffix},
            headers=headers,
        )
        assert summaries.status_code == 200
        summary_covers = {item["cover_number"] for item in summaries.get_json()["items"]}
        assert active_cover in summary_covers
        assert inactive_cover not in summary_covers

        details = client.get(
            "/admin/invoice-details",
            query_string={"search": suffix},
            headers=headers,
        )
        assert details.status_code == 200
        detail_numbers = {item["invoice_no"] for item in details.get_json()["items"]}
        assert active_invoice in detail_numbers
        assert inactive_invoice not in detail_numbers
    finally:
        with app_ctx.app_context():
            for invoice_no in (active_invoice, inactive_invoice):
                for detail in InvoiceDetail.query.filter_by(invoice_no=invoice_no).all():
                    db.session.delete(detail)
            for cover in (active_cover, inactive_cover):
                for summary in InvoiceSummary.query.filter_by(cover_number=cover).all():
                    db.session.delete(summary)
            user = User.query.filter_by(username=staff_user).first()
            if user:
                db.session.delete(user)
            for detail_code in (active_dc, inactive_dc):
                contractor = Contractor.query.filter_by(detail_code=detail_code).first()
                if contractor:
                    db.session.delete(contractor)
            db.session.commit()


def test_filter_options_are_scoped_to_contractor(client, app_ctx):
    suffix = _id_suffix()
    dc_a = f"id_{suffix}a"[:32]
    dc_b = f"id_{suffix}b"[:32]
    cover_a = f"ID-A-{suffix}"
    cover_b = f"ID-B-{suffix}"
    supplier = "66"
    username = f"inv_filter_{suffix}"

    with app_ctx.app_context():
        c_a = Contractor(
            detail_code=dc_a,
            supplier_code=supplier,
            name="Filter A",
            status="ظپط¹ط§ظ„",
            type="test",
        )
        c_b = Contractor(
            detail_code=dc_b,
            supplier_code=supplier,
            name="Filter B",
            status="ظپط¹ط§ظ„",
            type="test",
        )
        c_a.status = "\u0641\u0639\u0627\u0644"
        c_b.status = "\u0641\u0639\u0627\u0644"
        db.session.add_all([c_a, c_b])
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=c_a.id,
                    detail_code=dc_a,
                    supplier_code=supplier,
                    cover_number=cover_a,
                    invoice_created_at=date(2024, 9, 1),
                    invoice_status="own-filter-status",
                ),
                InvoiceSummary(
                    contractor_id=c_b.id,
                    detail_code=dc_b,
                    supplier_code=supplier,
                    cover_number=cover_b,
                    invoice_created_at=date(2024, 9, 2),
                    invoice_status="other-filter-status",
                ),
            ]
        )
        user = User(
            username=username,
            contractor_id=c_a.id,
            role="contractor",
            must_change_password=False,
        )
        user.set_password("filter-pass-12")
        db.session.add(user)
        db.session.commit()

    try:
        login = client.post(
            "/auth/login",
            json={"username": username, "password": "filter-pass-12"},
        )
        assert login.status_code == 200
        token = login.get_json()["access_token"]
        res = client.get(
            "/invoices/filters/options",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert "own-filter-status" in body["statuses"]
        assert "other-filter-status" not in body["statuses"]
        assert body["status_stats"]["own-filter-status"]["count"] == 1
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
