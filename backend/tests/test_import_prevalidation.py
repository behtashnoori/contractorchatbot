"""Import prevalidation tests: invalid files must not delete existing data."""

from __future__ import annotations

import os
from io import BytesIO

import pandas as pd
import pytest

from app.extensions import db
from app.models import Contractor, ImportBatch, ImportError, InvoiceDetail, InvoiceSummary, User
from app.constants.import_status import STATUS_DONE
from app.services.codtafsiltamin_importer import CodTafsiltaminImporter, EXPECTED_COLUMNS
from app.services.contractors_one_importer import ContractorsOneImporter
from app.services.contractors_two_importer import ContractorsTwoImporter
from app.services.import_activation import rollback_source_to_batch
from app.services.template_generator import (
    generate_contractors_one_template,
    generate_contractors_two_template,
)

pytestmark = pytest.mark.skipif(
    not (os.environ.get("TEST_DATABASE_URL") or "").strip(),
    reason="TEST_DATABASE_URL not set; see docs/TEST_DATABASE_SETUP.md",
)


def _xlsx_frame(rows: list[dict]) -> BytesIO:
    output = BytesIO()
    pd.DataFrame(rows).to_excel(output, index=False)
    output.seek(0)
    return output


def _batch(source: str) -> ImportBatch:
    batch = ImportBatch(name=f"pytest-{source}", source=source, status="pending")
    db.session.add(batch)
    db.session.commit()
    return batch


def test_codtafsiltamin_successful_import_creates_contractors(app_ctx):
    with app_ctx.app_context():
        db.session.query(InvoiceDetail).delete()
        db.session.query(InvoiceSummary).delete()
        db.session.query(User).delete()
        db.session.query(Contractor).delete()
        db.session.commit()

        batch = _batch("codtafsiltamin")
        file_obj = _xlsx_frame(
            [
                {
                    EXPECTED_COLUMNS[0]: "732",
                    EXPECTED_COLUMNS[1]: "Pytest Supplier",
                    EXPECTED_COLUMNS[2]: "active",
                    EXPECTED_COLUMNS[3]: "test",
                    EXPECTED_COLUMNS[4]: "26968",
                }
            ]
        )

        result = CodTafsiltaminImporter(batch).run(file_obj)

        assert result.inserted == 1
        assert result.errors == 0
        contractor = Contractor.query.filter_by(detail_code="26968").one()
        assert contractor.supplier_code == "732"
        assert contractor.name == "Pytest Supplier"
        assert contractor.is_active is True
        assert contractor.last_update_batch_id == batch.id

        db.session.delete(contractor)
        db.session.delete(batch)
        db.session.commit()


def test_codtafsiltamin_second_import_transfers_matching_user_and_rejects_removed_contractor_token(
    client,
    app_ctx,
):
    with app_ctx.app_context():
        db.session.query(User).filter(User.username.in_(["cod-transfer-user", "cod-removed-user"])).delete(
            synchronize_session=False
        )
        for detail_code in ("cod-transfer", "cod-removed"):
            for contractor in Contractor.query.filter_by(detail_code=detail_code).all():
                db.session.delete(contractor)
        db.session.commit()

        batch_one = _batch("codtafsiltamin")
        first_file = _xlsx_frame(
            [
                {
                    EXPECTED_COLUMNS[0]: "732",
                    EXPECTED_COLUMNS[1]: "Transfer Supplier Old",
                    EXPECTED_COLUMNS[2]: "فعال",
                    EXPECTED_COLUMNS[3]: "test",
                    EXPECTED_COLUMNS[4]: "cod-transfer",
                },
                {
                    EXPECTED_COLUMNS[0]: "733",
                    EXPECTED_COLUMNS[1]: "Removed Supplier",
                    EXPECTED_COLUMNS[2]: "فعال",
                    EXPECTED_COLUMNS[3]: "test",
                    EXPECTED_COLUMNS[4]: "cod-removed",
                },
            ]
        )
        assert CodTafsiltaminImporter(batch_one).run(first_file).inserted == 2
        batch_one_id = batch_one.id

        old_transfer = Contractor.query.filter_by(detail_code="cod-transfer", is_active=True).one()
        removed = Contractor.query.filter_by(detail_code="cod-removed", is_active=True).one()
        transfer_user = User(
            username="cod-transfer-user",
            contractor_id=old_transfer.id,
            role="contractor",
            must_change_password=False,
        )
        transfer_user.set_password("transfer-pass-12")
        removed_user = User(
            username="cod-removed-user",
            contractor_id=removed.id,
            role="contractor",
            must_change_password=False,
        )
        removed_user.set_password("removed-pass-12")
        db.session.add_all([transfer_user, removed_user])
        db.session.commit()

    removed_login = client.post(
        "/auth/login",
        json={"username": "cod-removed-user", "password": "removed-pass-12"},
    )
    assert removed_login.status_code == 200
    removed_token = removed_login.get_json()["access_token"]

    with app_ctx.app_context():
        batch_two = _batch("codtafsiltamin")
        second_file = _xlsx_frame(
            [
                {
                    EXPECTED_COLUMNS[0]: "999",
                    EXPECTED_COLUMNS[1]: "Transfer Supplier New",
                    EXPECTED_COLUMNS[2]: "فعال",
                    EXPECTED_COLUMNS[3]: "test",
                    EXPECTED_COLUMNS[4]: "cod-transfer",
                }
            ]
        )
        assert CodTafsiltaminImporter(batch_two).run(second_file).inserted == 1
        batch_two_id = batch_two.id

        active_transfer = Contractor.query.filter_by(detail_code="cod-transfer", is_active=True).one()
        inactive_transfer = Contractor.query.filter_by(
            detail_code="cod-transfer",
            is_active=False,
        ).one()
        inactive_removed = Contractor.query.filter_by(detail_code="cod-removed", is_active=False).one()
        transfer_user = User.query.filter_by(username="cod-transfer-user").one()

        assert active_transfer.last_update_batch_id == batch_two_id
        assert inactive_transfer.last_update_batch_id == batch_one_id
        assert transfer_user.contractor_id == active_transfer.id
        assert inactive_removed.last_update_batch_id == batch_one_id
        assert ImportBatch.query.filter_by(id=batch_one_id).count() == 1
        assert ImportBatch.query.filter_by(id=batch_two_id).count() == 1

    stale_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {removed_token}"},
    )
    assert stale_response.status_code == 403

    with app_ctx.app_context():
        for username in ("cod-transfer-user", "cod-removed-user"):
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)
        for detail_code in ("cod-transfer", "cod-removed"):
            for contractor in Contractor.query.filter_by(detail_code=detail_code).all():
                db.session.delete(contractor)
        ImportBatch.query.filter(ImportBatch.id.in_([batch_one_id, batch_two_id])).update(
            {ImportBatch.replaced_by_batch_id: None},
            synchronize_session=False,
        )
        for batch_id in (batch_two_id, batch_one_id):
            batch = db.session.get(ImportBatch, batch_id)
            if batch:
                db.session.delete(batch)
        db.session.commit()


def test_codtafsiltamin_invalid_header_preserves_existing_contractors(app_ctx):
    with app_ctx.app_context():
        existing = Contractor(
            detail_code="keep-cod-prevalidation",
            supplier_code="keep-supplier",
            name="Keep Contractor",
            status="active",
            type="test",
        )
        db.session.add(existing)
        batch = _batch("codtafsiltamin")
        before_count = Contractor.query.filter_by(detail_code=existing.detail_code).count()

        with pytest.raises(ValueError):
            CodTafsiltaminImporter(batch).run(_xlsx_frame([{"bad_header": "value"}]))

        assert before_count == 1
        assert Contractor.query.filter_by(detail_code=existing.detail_code).count() == 1

        db.session.delete(existing)
        db.session.delete(batch)
        db.session.commit()


def test_codtafsiltamin_publish_error_rolls_back_deleted_dataset(app_ctx, monkeypatch):
    with app_ctx.app_context():
        existing = Contractor(
            detail_code="keep-cod-publish-fail",
            supplier_code="keep-supplier",
            name="Keep Contractor",
            status="active",
            type="test",
        )
        db.session.add(existing)
        batch = _batch("codtafsiltamin")
        original_add = db.session.add

        def fail_new_contractor_add(instance, *args, **kwargs):
            if isinstance(instance, Contractor) and instance.detail_code == "26968":
                raise RuntimeError("simulated codtafsiltamin publish failure")
            return original_add(instance, *args, **kwargs)

        monkeypatch.setattr(db.session, "add", fail_new_contractor_add)

        file_obj = _xlsx_frame(
            [
                {
                    EXPECTED_COLUMNS[0]: "732",
                    EXPECTED_COLUMNS[1]: "Pytest Supplier",
                    EXPECTED_COLUMNS[2]: "active",
                    EXPECTED_COLUMNS[3]: "test",
                    EXPECTED_COLUMNS[4]: "26968",
                }
            ]
        )

        with pytest.raises(RuntimeError, match="simulated codtafsiltamin publish failure"):
            CodTafsiltaminImporter(batch).run(file_obj)

        assert Contractor.query.filter_by(detail_code="keep-cod-publish-fail").count() == 1

        db.session.delete(existing)
        db.session.delete(batch)
        db.session.commit()


def test_contractors_one_invalid_header_preserves_existing_invoice_data(app_ctx):
    with app_ctx.app_context():
        summary = InvoiceSummary(
            cover_number="keep-c1-prevalidation",
            invoice_status="existing",
            detail_code="keep-dc",
            supplier_code="keep-sc",
        )
        detail = InvoiceDetail(
            cover_number="keep-c1-prevalidation",
            invoice_no="keep-c1-prevalidation-1",
            status="existing",
        )
        db.session.add_all([summary, detail])
        batch = _batch("contractors-1")

        with pytest.raises(ValueError):
            ContractorsOneImporter(batch).run(_xlsx_frame([{"bad_header": "value"}]))

        assert InvoiceSummary.query.filter_by(cover_number="keep-c1-prevalidation").count() == 1
        assert InvoiceDetail.query.filter_by(cover_number="keep-c1-prevalidation").count() == 1

        db.session.delete(detail)
        db.session.delete(summary)
        db.session.delete(batch)
        db.session.commit()


def test_contractors_one_successful_import_uses_preflight_data(app_ctx):
    with app_ctx.app_context():
        batch = _batch("contractors-1")

        result = ContractorsOneImporter(batch).run(generate_contractors_one_template())

        assert result.inserted == 2
        assert result.errors == 0
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch.id).count() == 2
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch.id, is_active=True).count() == 2
        assert batch.total_rows == 2
        assert batch.rows_processed == 2
        assert batch.progress_percentage == 100.0
        assert batch.published_at is not None

        InvoiceSummary.query.filter_by(last_update_batch_id=batch.id).delete()
        db.session.delete(batch)
        db.session.commit()


def test_contractors_one_second_successful_import_activates_new_batch_and_keeps_history(app_ctx):
    with app_ctx.app_context():
        batch_one = _batch("contractors-1")
        batch_two = _batch("contractors-1")
        old_error = ImportError(
            batch_id=batch_one.id,
            source_file="contractors-1",
            row_index=99,
            message="old error",
            payload={"old": True},
        )
        db.session.add(old_error)
        db.session.commit()

        first = ContractorsOneImporter(batch_one).run(generate_contractors_one_template())
        second = ContractorsOneImporter(batch_two).run(generate_contractors_one_template())

        assert first.inserted == 2
        assert second.inserted == 2
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch_one.id).count() == 2
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch_one.id, is_active=True).count() == 0
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch_two.id, is_active=True).count() == 2
        assert ImportError.query.filter_by(id=old_error.id).count() == 1
        assert ImportBatch.query.filter_by(id=batch_one.id).count() == 1
        assert ImportBatch.query.filter_by(id=batch_two.id).count() == 1
        assert batch_one.replaced_by_batch_id == batch_two.id

        batch_one.status = STATUS_DONE
        batch_two.status = STATUS_DONE
        db.session.commit()
        rollback_source_to_batch("contractors-1", batch_one.id)
        db.session.commit()
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch_one.id, is_active=True).count() == 2
        assert InvoiceSummary.query.filter_by(last_update_batch_id=batch_two.id, is_active=True).count() == 0

        InvoiceSummary.query.filter(InvoiceSummary.last_update_batch_id.in_([batch_one.id, batch_two.id])).delete(
            synchronize_session=False
        )
        ImportError.query.filter_by(id=old_error.id).delete()
        ImportBatch.query.filter(ImportBatch.id.in_([batch_one.id, batch_two.id])).update(
            {ImportBatch.replaced_by_batch_id: None},
            synchronize_session=False,
        )
        db.session.delete(batch_two)
        db.session.delete(batch_one)
        db.session.commit()


def test_contractors_one_publish_error_rolls_back_deleted_dataset(app_ctx, monkeypatch):
    with app_ctx.app_context():
        existing = InvoiceSummary(
            cover_number="keep-c1-publish-fail",
            invoice_status="existing",
            detail_code="keep-dc",
            supplier_code="keep-sc",
        )
        db.session.add(existing)
        batch = _batch("contractors-1")
        original_bulk_insert = db.session.bulk_insert_mappings

        def fail_invoice_summary_insert(model, mappings, *args, **kwargs):
            if model is InvoiceSummary:
                raise RuntimeError("simulated publish failure")
            return original_bulk_insert(model, mappings, *args, **kwargs)

        monkeypatch.setattr(db.session, "bulk_insert_mappings", fail_invoice_summary_insert)

        with pytest.raises(RuntimeError, match="simulated publish failure"):
            ContractorsOneImporter(batch).run(generate_contractors_one_template())

        assert InvoiceSummary.query.filter_by(cover_number="keep-c1-publish-fail").count() == 1
        assert InvoiceSummary.query.filter_by(cover_number="keep-c1-publish-fail", is_active=True).count() == 1

        db.session.delete(existing)
        db.session.delete(batch)
        db.session.commit()


def test_contractors_two_invalid_header_preserves_existing_details(app_ctx):
    with app_ctx.app_context():
        detail = InvoiceDetail(
            cover_number="keep-c2-prevalidation",
            invoice_no="keep-c2-prevalidation-1",
            status="existing",
        )
        db.session.add(detail)
        batch = _batch("contractors-2")

        with pytest.raises(ValueError):
            ContractorsTwoImporter(batch).run(_xlsx_frame([{"bad_header": "value"}]))

        assert InvoiceDetail.query.filter_by(cover_number="keep-c2-prevalidation").count() == 1

        db.session.delete(detail)
        db.session.delete(batch)
        db.session.commit()


def test_contractors_two_successful_import_uses_preflight_data(app_ctx):
    with app_ctx.app_context():
        summary_a = InvoiceSummary(
            cover_number="14040450",
            invoice_status="existing",
            detail_code="dt-a",
            supplier_code="sp-a",
        )
        summary_b = InvoiceSummary(
            cover_number="14040453",
            invoice_status="existing",
            detail_code="dt-b",
            supplier_code="sp-b",
        )
        db.session.add_all([summary_a, summary_b])
        batch = _batch("contractors-2")

        result = ContractorsTwoImporter(batch).run(generate_contractors_two_template())

        assert result.inserted == 2
        assert result.errors == 0
        assert InvoiceDetail.query.filter_by(last_update_batch_id=batch.id).count() == 2
        assert InvoiceDetail.query.filter_by(last_update_batch_id=batch.id, is_active=True).count() == 2
        assert batch.total_rows == 2
        assert batch.rows_processed == 2
        assert batch.progress_percentage == 100.0
        assert batch.published_at is not None

        InvoiceDetail.query.filter_by(last_update_batch_id=batch.id).delete()
        db.session.delete(summary_a)
        db.session.delete(summary_b)
        db.session.delete(batch)
        db.session.commit()


def test_contractors_two_second_successful_import_activates_new_batch_and_keeps_history(app_ctx):
    with app_ctx.app_context():
        summary_a = InvoiceSummary(
            cover_number="14040450",
            invoice_status="existing",
            detail_code="dt-a",
            supplier_code="sp-a",
            is_active=True,
        )
        summary_b = InvoiceSummary(
            cover_number="14040453",
            invoice_status="existing",
            detail_code="dt-b",
            supplier_code="sp-b",
            is_active=True,
        )
        db.session.add_all([summary_a, summary_b])
        batch_one = _batch("contractors-2")
        batch_two = _batch("contractors-2")
        old_error = ImportError(
            batch_id=batch_one.id,
            source_file="contractors-2",
            row_index=99,
            message="old detail error",
            payload={"old": True},
        )
        db.session.add(old_error)
        db.session.commit()

        first = ContractorsTwoImporter(batch_one).run(generate_contractors_two_template())
        second = ContractorsTwoImporter(batch_two).run(generate_contractors_two_template())

        assert first.inserted == 2
        assert second.inserted == 2
        assert InvoiceDetail.query.filter_by(last_update_batch_id=batch_one.id).count() == 2
        assert InvoiceDetail.query.filter_by(last_update_batch_id=batch_one.id, is_active=True).count() == 0
        assert InvoiceDetail.query.filter_by(last_update_batch_id=batch_two.id, is_active=True).count() == 2
        assert ImportError.query.filter_by(id=old_error.id).count() == 1
        assert ImportBatch.query.filter_by(id=batch_one.id).count() == 1
        assert ImportBatch.query.filter_by(id=batch_two.id).count() == 1
        assert batch_one.replaced_by_batch_id == batch_two.id

        InvoiceDetail.query.filter(InvoiceDetail.last_update_batch_id.in_([batch_one.id, batch_two.id])).delete(
            synchronize_session=False
        )
        ImportError.query.filter_by(id=old_error.id).delete()
        ImportBatch.query.filter(ImportBatch.id.in_([batch_one.id, batch_two.id])).update(
            {ImportBatch.replaced_by_batch_id: None},
            synchronize_session=False,
        )
        db.session.delete(summary_a)
        db.session.delete(summary_b)
        db.session.delete(batch_two)
        db.session.delete(batch_one)
        db.session.commit()


def test_contractors_two_publish_error_rolls_back_deleted_dataset(app_ctx, monkeypatch):
    with app_ctx.app_context():
        existing = InvoiceDetail(
            cover_number="keep-c2-publish-fail",
            invoice_no="keep-c2-publish-fail-1",
            status="existing",
        )
        summary_a = InvoiceSummary(
            cover_number="14040450",
            invoice_status="existing",
            detail_code="dt-a",
            supplier_code="sp-a",
        )
        summary_b = InvoiceSummary(
            cover_number="14040453",
            invoice_status="existing",
            detail_code="dt-b",
            supplier_code="sp-b",
        )
        db.session.add_all([existing, summary_a, summary_b])
        batch = _batch("contractors-2")
        original_bulk_insert = db.session.bulk_insert_mappings

        def fail_invoice_detail_insert(model, mappings, *args, **kwargs):
            if model is InvoiceDetail:
                raise RuntimeError("simulated publish failure")
            return original_bulk_insert(model, mappings, *args, **kwargs)

        monkeypatch.setattr(db.session, "bulk_insert_mappings", fail_invoice_detail_insert)

        with pytest.raises(RuntimeError, match="simulated publish failure"):
            ContractorsTwoImporter(batch).run(generate_contractors_two_template())

        assert InvoiceDetail.query.filter_by(cover_number="keep-c2-publish-fail").count() == 1
        assert InvoiceDetail.query.filter_by(cover_number="keep-c2-publish-fail", is_active=True).count() == 1

        db.session.delete(existing)
        db.session.delete(summary_a)
        db.session.delete(summary_b)
        db.session.delete(batch)
        db.session.commit()
