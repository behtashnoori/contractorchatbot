"""Integration tests for controlled import rollback (PostgreSQL via TEST_DATABASE_URL)."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime

import pytest

from app.constants.import_status import STATUS_DONE, STATUS_FAILED
from app.extensions import db
from app.models import (
    AuditLog,
    Contractor,
    ImportBatch,
    ImportError,
    InvoiceDetail,
    InvoiceSummary,
    User,
)
from app.services.audit_log import ACTION_IMPORT_ROLLBACK
from app.services.audit_log import ACTION_IMPORT_ROLLBACK_FAILED

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="TEST_DATABASE_URL not set; see docs/TEST_DATABASE_SETUP.md",
)


def _id_suffix() -> str:
    return uuid.uuid4().hex[:12]


def _active_status() -> str:
    return "\u0641\u0639\u0627\u0644"


def _login_headers(client, username: str, password: str) -> dict[str, str]:
    login = client.post("/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.get_json()['access_token']}"}


def _create_user(username: str, password: str, role: str, contractor_id=None) -> User:
    user = User(
        username=username,
        role=role,
        contractor_id=contractor_id,
        must_change_password=False,
    )
    user.set_password(password)
    db.session.add(user)
    return user


def _batch(source: str, suffix: str, status: str = STATUS_DONE, published: bool = True) -> ImportBatch:
    batch = ImportBatch(
        name=f"rollback-{source}-{suffix}-{uuid.uuid4().hex[:8]}",
        source=source,
        status=status,
        uploaded_by="pytest",
        published_at=datetime.now(UTC).replace(tzinfo=None) if published else None,
    )
    db.session.add(batch)
    db.session.flush()
    return batch


def _post_rollback(client, headers: dict[str, str], source: str, batch_id) -> object:
    return client.post(
        "/admin/imports/rollback",
        json={"source": source, "target_batch_id": str(batch_id)},
        headers=headers,
    )


def _cleanup(batch_ids=(), usernames=(), detail_codes=(), covers=(), invoice_numbers=()):
    if batch_ids:
        ImportBatch.query.filter(ImportBatch.replaced_by_batch_id.in_(batch_ids)).update(
            {ImportBatch.replaced_by_batch_id: None},
            synchronize_session=False,
        )
        ImportBatch.query.filter(ImportBatch.id.in_(batch_ids)).update(
            {ImportBatch.replaced_by_batch_id: None},
            synchronize_session=False,
        )
        db.session.flush()

    if batch_ids:
        AuditLog.query.filter(
            AuditLog.action.in_([ACTION_IMPORT_ROLLBACK, ACTION_IMPORT_ROLLBACK_FAILED]),
            AuditLog.entity_id.in_([batch_id.hex for batch_id in batch_ids]),
        ).delete(synchronize_session=False)
        ImportError.query.filter(ImportError.batch_id.in_(batch_ids)).delete(
            synchronize_session=False
        )
        InvoiceDetail.query.filter(InvoiceDetail.last_update_batch_id.in_(batch_ids)).delete(
            synchronize_session=False
        )
        InvoiceSummary.query.filter(InvoiceSummary.last_update_batch_id.in_(batch_ids)).delete(
            synchronize_session=False
        )

    if invoice_numbers:
        InvoiceDetail.query.filter(InvoiceDetail.invoice_no.in_(invoice_numbers)).delete(
            synchronize_session=False
        )
    if covers:
        InvoiceDetail.query.filter(InvoiceDetail.cover_number.in_(covers)).delete(
            synchronize_session=False
        )
        InvoiceSummary.query.filter(InvoiceSummary.cover_number.in_(covers)).delete(
            synchronize_session=False
        )
    if usernames:
        User.query.filter(User.username.in_(usernames)).delete(synchronize_session=False)
    if batch_ids:
        Contractor.query.filter(Contractor.last_update_batch_id.in_(batch_ids)).delete(
            synchronize_session=False
        )
    if detail_codes:
        Contractor.query.filter(Contractor.detail_code.in_(detail_codes)).delete(
            synchronize_session=False
        )
    if batch_ids:
        ImportBatch.query.filter(ImportBatch.id.in_(batch_ids)).delete(synchronize_session=False)
    db.session.commit()


def test_staff_can_rollback_contractors_one_and_active_rows_switch(client, app):
    suffix = _id_suffix()
    staff_username = f"rb_staff_{suffix}"
    contractor_username = f"rb_co_{suffix}"
    detail_code = f"rb_{suffix}"[:32]
    old_cover = f"RB-OLD-{suffix}"
    new_cover = f"RB-NEW-{suffix}"
    old_invoice = f"RB-D-OLD-{suffix}"
    new_invoice = f"RB-D-NEW-{suffix}"

    with app.app_context():
        batch_one = _batch("contractors-1", suffix)
        batch_two = _batch("contractors-1", suffix)
        batch_one.replaced_by_batch_id = batch_two.id
        contractor = Contractor(
            detail_code=detail_code,
            supplier_code="11",
            name=f"Rollback Contractor {suffix}",
            status=_active_status(),
            type="test",
            is_active=True,
        )
        db.session.add(contractor)
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="11",
                    cover_number=old_cover,
                    invoice_created_at=date(2024, 1, 1),
                    invoice_status="old-visible-after-rollback",
                    last_update_batch_id=batch_one.id,
                    is_active=False,
                ),
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="11",
                    cover_number=new_cover,
                    invoice_created_at=date(2024, 1, 2),
                    invoice_status="new-hidden-after-rollback",
                    last_update_batch_id=batch_two.id,
                    is_active=True,
                ),
                InvoiceDetail(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="11",
                    cover_number=old_cover,
                    invoice_no=old_invoice,
                    status="old-detail",
                    last_update_batch_id=batch_one.id,
                    is_active=False,
                ),
                InvoiceDetail(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="11",
                    cover_number=new_cover,
                    invoice_no=new_invoice,
                    status="new-detail",
                    last_update_batch_id=batch_two.id,
                    is_active=True,
                ),
            ]
        )
        _create_user(staff_username, "staff-rollback-pass-12", "staff")
        _create_user(contractor_username, "contractor-rollback-pass-12", "contractor", contractor.id)
        db.session.commit()
        batch_one_id = batch_one.id
        batch_two_id = batch_two.id

    try:
        staff_headers = _login_headers(client, staff_username, "staff-rollback-pass-12")
        response = _post_rollback(client, staff_headers, "contractors-1", batch_one_id)
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "rolled_back"
        assert body["source"] == "contractors-1"
        assert body["target_batch_id"] == batch_one_id.hex
        assert batch_two_id.hex in body["previous_active_batch_ids"]
        assert body["activated_counts"]["invoicesummary"] == 1
        assert body["activated_counts"]["invoicedetail"] == 1

        with app.app_context():
            assert InvoiceSummary.query.filter_by(cover_number=old_cover).first().is_active is True
            assert InvoiceSummary.query.filter_by(cover_number=new_cover).first().is_active is False
            assert InvoiceDetail.query.filter_by(invoice_no=old_invoice).first().is_active is True
            assert InvoiceDetail.query.filter_by(invoice_no=new_invoice).first().is_active is False
            assert db.session.get(ImportBatch, batch_one_id).replaced_by_batch_id is None
            assert db.session.get(ImportBatch, batch_two_id).replaced_by_batch_id == batch_one_id
            assert (
                AuditLog.query.filter_by(
                    action=ACTION_IMPORT_ROLLBACK,
                    entity="import_batch",
                    entity_id=batch_one_id.hex,
                ).count()
                == 1
            )

        contractor_headers = _login_headers(
            client, contractor_username, "contractor-rollback-pass-12"
        )
        invoices = client.get("/invoices/", headers=contractor_headers)
        assert invoices.status_code == 200
        covers = {item["cover_number"] for item in invoices.get_json()["items"]}
        assert old_cover in covers
        assert new_cover not in covers
    finally:
        with app.app_context():
            _cleanup(
                batch_ids=(batch_one_id, batch_two_id),
                usernames=(staff_username, contractor_username),
                detail_codes=(detail_code,),
                covers=(old_cover, new_cover),
                invoice_numbers=(old_invoice, new_invoice),
            )


def test_contractor_and_stale_demoted_staff_cannot_rollback(client, app):
    suffix = _id_suffix()
    contractor_username = f"rb_forbid_{suffix}"
    staff_username = f"rb_demote_{suffix}"
    detail_code = f"rbd_{suffix}"[:32]

    with app.app_context():
        target_batch = _batch("contractors-1", suffix)
        contractor = Contractor(
            detail_code=detail_code,
            supplier_code="12",
            name=f"Rollback Forbidden {suffix}",
            status=_active_status(),
            type="test",
            is_active=True,
        )
        db.session.add(contractor)
        db.session.flush()
        _create_user(
            contractor_username,
            "contractor-forbid-pass-12",
            "contractor",
            contractor.id,
        )
        staff = _create_user(staff_username, "staff-demote-pass-12", "staff")
        db.session.commit()
        target_batch_id = target_batch.id
        staff_id = staff.id

    try:
        contractor_headers = _login_headers(client, contractor_username, "contractor-forbid-pass-12")
        contractor_response = _post_rollback(
            client, contractor_headers, "contractors-1", target_batch_id
        )
        assert contractor_response.status_code == 403

        staff_headers = _login_headers(client, staff_username, "staff-demote-pass-12")
        with app.app_context():
            user = db.session.get(User, staff_id)
            user.role = "contractor"
            user.contractor_id = Contractor.query.filter_by(detail_code=detail_code).first().id
            db.session.commit()
            db.session.remove()

        stale_response = _post_rollback(client, staff_headers, "contractors-1", target_batch_id)
        assert stale_response.status_code == 403
    finally:
        with app.app_context():
            _cleanup(
                batch_ids=(target_batch_id,),
                usernames=(contractor_username, staff_username),
                detail_codes=(detail_code,),
            )


def test_rollback_validates_target_source_status_and_existence(client, app):
    suffix = _id_suffix()
    staff_username = f"rb_validate_{suffix}"

    with app.app_context():
        done_batch = _batch("contractors-1", suffix)
        failed_batch = _batch("contractors-1", suffix, status=STATUS_FAILED)
        _create_user(staff_username, "staff-validate-pass-12", "staff")
        db.session.commit()
        done_batch_id = done_batch.id
        failed_batch_id = failed_batch.id

    try:
        headers = _login_headers(client, staff_username, "staff-validate-pass-12")

        missing_batch_id = uuid.uuid4()
        missing = _post_rollback(client, headers, "contractors-1", missing_batch_id)
        assert missing.status_code == 404

        invalid_source = _post_rollback(client, headers, "contractors-2", done_batch_id)
        assert invalid_source.status_code == 400
        assert invalid_source.get_json()["error"] == "invalid_rollback_target"
        with app.app_context():
            assert (
                AuditLog.query.filter_by(
                    action=ACTION_IMPORT_ROLLBACK_FAILED,
                    entity="import_batch",
                    entity_id=done_batch_id.hex,
                ).count()
                == 1
            )

        invalid_status = _post_rollback(client, headers, "contractors-1", failed_batch_id)
        assert invalid_status.status_code == 400
        assert invalid_status.get_json()["error"] == "invalid_rollback_target"
        with app.app_context():
            assert (
                AuditLog.query.filter_by(
                    action=ACTION_IMPORT_ROLLBACK_FAILED,
                    entity="import_batch",
                    entity_id=failed_batch_id.hex,
                ).count()
                == 1
            )

        empty_done_batch = _post_rollback(client, headers, "contractors-1", done_batch_id)
        assert empty_done_batch.status_code == 400
        assert empty_done_batch.get_json()["error"] == "invalid_rollback_target"
    finally:
        with app.app_context():
            _cleanup(
                batch_ids=(done_batch_id, failed_batch_id, missing_batch_id),
                usernames=(staff_username,),
            )


def test_rollback_failure_preserves_previous_active_rows(client, app, monkeypatch):
    suffix = _id_suffix()
    staff_username = f"rb_tx_{suffix}"
    detail_code = f"rbtx_{suffix}"[:32]
    old_cover = f"RB-TX-OLD-{suffix}"
    new_cover = f"RB-TX-NEW-{suffix}"

    with app.app_context():
        batch_one = _batch("contractors-1", suffix)
        batch_two = _batch("contractors-1", suffix)
        contractor = Contractor(
            detail_code=detail_code,
            supplier_code="13",
            name=f"Rollback Tx {suffix}",
            status=_active_status(),
            type="test",
            is_active=True,
        )
        db.session.add(contractor)
        db.session.flush()
        db.session.add_all(
            [
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="13",
                    cover_number=old_cover,
                    invoice_status="old-tx",
                    last_update_batch_id=batch_one.id,
                    is_active=False,
                ),
                InvoiceSummary(
                    contractor_id=contractor.id,
                    detail_code=detail_code,
                    supplier_code="13",
                    cover_number=new_cover,
                    invoice_status="new-tx",
                    last_update_batch_id=batch_two.id,
                    is_active=True,
                ),
            ]
        )
        _create_user(staff_username, "staff-tx-pass-12", "staff")
        db.session.commit()
        batch_one_id = batch_one.id
        batch_two_id = batch_two.id

    def fail_after_partial_change(source, batch_id):
        InvoiceSummary.query.filter_by(cover_number=new_cover).update(
            {InvoiceSummary.is_active: False},
            synchronize_session=False,
        )
        raise RuntimeError("simulated rollback failure")

    try:
        from app.routes import admin as admin_routes

        monkeypatch.setattr(admin_routes, "rollback_source_to_batch", fail_after_partial_change)
        headers = _login_headers(client, staff_username, "staff-tx-pass-12")
        response = _post_rollback(client, headers, "contractors-1", batch_one_id)
        assert response.status_code == 500

        with app.app_context():
            assert InvoiceSummary.query.filter_by(cover_number=old_cover).first().is_active is False
            assert InvoiceSummary.query.filter_by(cover_number=new_cover).first().is_active is True
            assert (
                AuditLog.query.filter_by(
                    action=ACTION_IMPORT_ROLLBACK_FAILED,
                    entity="import_batch",
                    entity_id=batch_one_id.hex,
                ).count()
                == 1
            )
    finally:
        with app.app_context():
            _cleanup(
                batch_ids=(batch_one_id, batch_two_id),
                usernames=(staff_username,),
                detail_codes=(detail_code,),
                covers=(old_cover, new_cover),
            )


def test_codtafsiltamin_rollback_relinks_user_and_preserves_batch_history(client, app):
    suffix = _id_suffix()
    staff_username = f"rb_cod_staff_{suffix}"
    contractor_username = f"rb_cod_user_{suffix}"
    detail_code = f"rbcod_{suffix}"[:32]

    with app.app_context():
        batch_one = _batch("codtafsiltamin", suffix)
        batch_two = _batch("codtafsiltamin", suffix)
        batch_one.replaced_by_batch_id = batch_two.id
        old_contractor = Contractor(
            detail_code=detail_code,
            supplier_code="14",
            name=f"Old Cod {suffix}",
            status=_active_status(),
            type="test",
            last_update_batch_id=batch_one.id,
            is_active=False,
        )
        new_contractor = Contractor(
            detail_code=detail_code,
            supplier_code="14",
            name=f"New Cod {suffix}",
            status=_active_status(),
            type="test",
            last_update_batch_id=batch_two.id,
            is_active=True,
        )
        db.session.add_all([old_contractor, new_contractor])
        db.session.flush()
        _create_user(staff_username, "staff-cod-pass-12", "staff")
        _create_user(
            contractor_username,
            "contractor-cod-pass-12",
            "contractor",
            new_contractor.id,
        )
        db.session.add(
            ImportError(
                batch_id=batch_one.id,
                source_file="pytest",
                row_index=1,
                message="preserve rollback history",
                payload={"test": True},
            )
        )
        db.session.commit()
        batch_one_id = batch_one.id
        batch_two_id = batch_two.id
        old_contractor_id = old_contractor.id
        new_contractor_id = new_contractor.id

    try:
        headers = _login_headers(client, staff_username, "staff-cod-pass-12")
        response = _post_rollback(client, headers, "codtafsiltamin", batch_one_id)
        assert response.status_code == 200
        assert response.get_json()["activated_counts"]["contractor"] == 1

        with app.app_context():
            assert db.session.get(Contractor, old_contractor_id).is_active is True
            assert db.session.get(Contractor, new_contractor_id).is_active is False
            user = User.query.filter_by(username=contractor_username).first()
            assert user.contractor_id == old_contractor_id
            assert db.session.get(ImportBatch, batch_one_id).replaced_by_batch_id is None
            assert db.session.get(ImportBatch, batch_two_id).replaced_by_batch_id == batch_one_id
            assert ImportError.query.filter_by(batch_id=batch_one_id).count() == 1
    finally:
        with app.app_context():
            _cleanup(
                batch_ids=(batch_one_id, batch_two_id),
                usernames=(staff_username, contractor_username),
                detail_codes=(detail_code,),
            )
