from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, g, jsonify, request, send_file

from uuid import UUID

from ..constants.import_status import (
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_PROCESSING,
    TERMINAL_STATUSES,
)
from ..extensions import db
from ..models import Contractor, ImportBatch, ImportError, User, InvoiceSummary, InvoiceDetail
from ..services.codtafsiltamin_importer import CodTafsiltaminImporter
from ..services.import_activation import active_query, rollback_source_to_batch
from ..utils.api_errors import error_response
from ..utils.auth_decorators import require_staff
from ..utils.auth_utils import generate_password, generate_username
from ..services.audit_log import (
    ACTION_IMPORT_UPLOAD,
    ACTION_IMPORT_ROLLBACK,
    ACTION_IMPORT_ROLLBACK_FAILED,
    ENTITY_IMPORT_BATCH,
    record_audit,
)
from ..services.contractors_one_importer import ContractorsOneImporter
from ..services.contractors_two_importer import ContractorsTwoImporter
from ..services.template_generator import (
    generate_codtafsiltamin_template,
    generate_contractors_one_template,
    generate_contractors_two_template,
)

admin_bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


def _utc_timestamp_name() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def _record_rollback_failure_audit(user_id, target_batch_id: UUID | None) -> None:
    try:
        record_audit(
            user_id,
            ACTION_IMPORT_ROLLBACK_FAILED,
            ENTITY_IMPORT_BATCH,
            target_batch_id.hex if target_batch_id else None,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Failed to record rollback failure audit")


def _process_file_background(batch_id: UUID, file_path: Path, source: str):
    """Background processing function for file imports"""
    # Import here to avoid circular imports
    from .. import create_app
    
    app = create_app()
    with app.app_context():
        batch = ImportBatch.query.get(batch_id)
        if not batch:
            logger.error("Background import: batch %s not found", batch_id)
            return

        logger.info("Background starting %s import for batch %s", source, batch_id)
        try:
            # Refresh batch to ensure we have the latest schema
            db.session.refresh(batch)

            batch.status = STATUS_PROCESSING
            db.session.commit()
            logger.info(
                "Import batch %s lifecycle: processing source=%s",
                batch_id,
                source,
            )

            # Open saved file
            with open(file_path, 'rb') as f:
                from werkzeug.datastructures import FileStorage
                file_obj = FileStorage(
                    stream=f,
                    filename=file_path.name,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                
                if source == "contractors-1":
                    importer = ContractorsOneImporter(batch)
                elif source == "contractors-2":
                    importer = ContractorsTwoImporter(batch)
                elif source == "codtafsiltamin":
                    importer = CodTafsiltaminImporter(batch)
                else:
                    raise ValueError(f"Unknown source: {source}")
                
                logger.info("Running importer for %s", source)
                result = importer.run(file_obj)
                logger.info(
                    "Importer completed: inserted=%s updated=%s errors=%s",
                    result.inserted,
                    result.updated,
                    result.errors,
                )
                
                # Refresh batch to get latest state
                db.session.refresh(batch)

                batch.status = STATUS_DONE

                # Update metrics
                batch.update_metrics(result.inserted, result.updated, result.errors)
                logger.info(
                    "Import batch %s lifecycle: done source=%s inserted=%s updated=%s errors=%s",
                    batch_id,
                    source,
                    result.inserted,
                    result.updated,
                    result.errors,
                )

        except ValueError as exc:
            error_id = str(uuid.uuid4())
            logger.exception("ValueError in %s import [%s]", source, error_id)
            db.session.rollback()
            batch = ImportBatch.query.get(batch_id)
            if batch:
                batch.status = STATUS_FAILED
                batch.notes = f"failed ({error_id})"
                db.session.commit()
                logger.info(
                    "Import batch %s lifecycle: failed source=%s error_id=%s",
                    batch_id,
                    source,
                    error_id,
                )
        except Exception as exc:
            error_id = str(uuid.uuid4())
            logger.exception("Exception in %s import [%s]", source, error_id)
            db.session.rollback()
            batch = ImportBatch.query.get(batch_id)
            if batch:
                batch.status = STATUS_FAILED
                batch.notes = f"failed ({error_id})"
                db.session.commit()
                logger.info(
                    "Import batch %s lifecycle: failed source=%s error_id=%s",
                    batch_id,
                    source,
                    error_id,
                )
        finally:
            # Clean up temporary file
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass


@admin_bp.post("/uploads")
@require_staff
def upload_batch():
    files = request.files
    if not files:
        return error_response(400, "no_files", "No files were uploaded.")

    # Placeholder batch (no file ingest on this path; use specific upload endpoints).
    batch = ImportBatch(name="manual-upload", source="manual", status=STATUS_PENDING)
    batch.uploaded_by = g.current_user.username

    db.session.add(batch)
    db.session.flush()
    record_audit(g.current_user.id, ACTION_IMPORT_UPLOAD, ENTITY_IMPORT_BATCH, batch.id.hex)
    db.session.commit()

    return jsonify({"batch_id": batch.id.hex, "status": batch.status}), 202


@admin_bp.post("/uploads/codtafsiltamin")
@require_staff
def upload_codtafsiltamin():
    file = request.files.get("file")
    if not file:
        return error_response(
            400,
            "file_required",
            "Multipart file field 'file' is required.",
        )

    batch = ImportBatch(
        name=f"codtafsiltamin-{_utc_timestamp_name()}",
        source="codtafsiltamin",
        status=STATUS_PENDING,
        uploaded_by=g.current_user.username,
    )
    db.session.add(batch)
    db.session.flush()
    record_audit(g.current_user.id, ACTION_IMPORT_UPLOAD, ENTITY_IMPORT_BATCH, batch.id.hex)
    db.session.commit()

    batch.status = STATUS_PROCESSING
    db.session.commit()
    logger.info(
        "Import batch %s lifecycle: processing source=codtafsiltamin",
        batch.id,
    )

    importer = CodTafsiltaminImporter(batch)
    try:
        result = importer.run(file)
    except ValueError:
        error_id = str(uuid.uuid4())
        logger.exception("ValueError in codtafsiltamin upload [%s]", error_id)
        db.session.rollback()
        batch_row = db.session.get(ImportBatch, batch.id)
        if batch_row:
            batch_row.status = STATUS_FAILED
            batch_row.notes = f"failed ({error_id})"
            db.session.commit()
            logger.info(
                "Import batch %s lifecycle: failed source=codtafsiltamin error_id=%s",
                batch.id,
                error_id,
            )
        return error_response(
            400,
            "invalid_file",
            "The file could not be processed.",
            error_id=error_id,
        )
    except Exception:
        error_id = str(uuid.uuid4())
        logger.exception("Exception in codtafsiltamin upload [%s]", error_id)
        db.session.rollback()
        batch_row = db.session.get(ImportBatch, batch.id)
        if batch_row:
            batch_row.status = STATUS_FAILED
            batch_row.notes = f"failed ({error_id})"
            db.session.commit()
            logger.info(
                "Import batch %s lifecycle: failed source=codtafsiltamin error_id=%s",
                batch.id,
                error_id,
            )
        return error_response(
            500,
            "internal_error",
            "An unexpected error occurred",
            error_id=error_id,
        )

    batch.status = STATUS_DONE
    batch.inserted_count = result.inserted
    batch.updated_count = result.updated
    batch.errors_count = result.errors
    db.session.commit()
    logger.info(
        "Import batch %s lifecycle: done source=codtafsiltamin inserted=%s updated=%s errors=%s",
        batch.id,
        result.inserted,
        result.updated,
        result.errors,
    )

    # Count total unique contractors in database
    total_contractors = active_query(Contractor).count()

    return (
        jsonify(
            {
                "batch_id": batch.id.hex,
                "status": batch.status,
                "metrics": {
                    "inserted": result.inserted,
                    "updated": result.updated,
                    "errors": result.errors,
                    "total_in_database": total_contractors,
                },
            }
        ),
        201,
    )


@admin_bp.post("/uploads/contractors-1")
@require_staff
def upload_contractors_one():
    file = request.files.get("file")
    if not file:
        return error_response(
            400,
            "file_required",
            "Multipart file field 'file' is required.",
        )

    try:
        # Save file to temporary location
        file_ext = os.path.splitext(file.filename)[1] or '.xlsx'
        temp_file = NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            dir=str(UPLOADS_DIR)
        )
        file.save(temp_file.name)
        file_path = Path(temp_file.name)

        # Create batch
        batch = ImportBatch(
            name=f"contractors-1-{_utc_timestamp_name()}",
            source="contractors-1",
            status=STATUS_PENDING,
            uploaded_by=g.current_user.username,
        )
        db.session.add(batch)
        db.session.flush()
        record_audit(g.current_user.id, ACTION_IMPORT_UPLOAD, ENTITY_IMPORT_BATCH, batch.id.hex)
        db.session.commit()

        # Start background processing
        thread = threading.Thread(
            target=_process_file_background,
            args=(batch.id, file_path, "contractors-1"),
            daemon=False
        )
        thread.start()

        # Return immediately with 202 Accepted
        return (
            jsonify(
                {
                    "batch_id": batch.id.hex,
                    "status": STATUS_PENDING,
                    "message": "File uploaded successfully. Processing in background.",
                }
            ),
            202,
        )
    except Exception:
        db.session.rollback()
        error_id = str(uuid.uuid4())
        logger.exception("contractors-1 upload failed [%s]", error_id)
        return error_response(
            500,
            "internal_error",
            "An unexpected error occurred",
            error_id=error_id,
        )


@admin_bp.get("/uploads/<batch_id>/progress")
@require_staff
def get_upload_progress(batch_id):
    """Get progress of an upload batch"""
    try:
        batch_uuid = UUID(batch_id) if isinstance(batch_id, str) else batch_id
    except (ValueError, TypeError):
        return error_response(
            400,
            "invalid_batch_id",
            "Batch id must be a valid UUID.",
        )

    batch = ImportBatch.query.get(batch_uuid)
    if not batch:
        return error_response(404, "not_found", "Batch not found.")
    
    # Get metrics - use stored values if available, otherwise calculate
    # Always return metrics, even during processing
    metrics = {
        "inserted": batch.inserted_count or 0,
        "updated": batch.updated_count or 0,
        "errors": batch.errors_count or 0,
    }
    
    # If metrics are zero but batch is finished, try to calculate from database
    if batch.status in TERMINAL_STATUSES:
        if metrics["inserted"] == 0 and metrics["updated"] == 0 and metrics["errors"] == 0:
            # Fallback: calculate from database
            if batch.source == "contractors-1":
                from ..models import InvoiceSummary
                metrics["inserted"] = InvoiceSummary.query.filter_by(last_update_batch_id=batch.id).count()
                metrics["errors"] = ImportError.query.filter_by(batch_id=batch.id).count()
            elif batch.source == "contractors-2":
                from ..models import InvoiceDetail
                metrics["inserted"] = InvoiceDetail.query.filter_by(last_update_batch_id=batch.id).count()
                metrics["errors"] = ImportError.query.filter_by(batch_id=batch.id).count()
            elif batch.source == "codtafsiltamin":
                metrics["errors"] = ImportError.query.filter_by(batch_id=batch.id).count()
    
    return jsonify({
        "batch_id": batch.id.hex,
        "status": batch.status,
        "terminal": batch.status in TERMINAL_STATUSES,
        "progress": {
            "percentage": batch.progress_percentage or 0.0,
            "processed": batch.rows_processed or 0,
            "total": batch.total_rows or 0,
        },
        "metrics": metrics,
    }), 200


@admin_bp.post("/imports/rollback")
@require_staff
def rollback_import_batch():
    payload = request.get_json(silent=True) or {}
    source = (payload.get("source") or "").strip()
    batch_id = payload.get("target_batch_id") or payload.get("batch_id")

    if not source or not batch_id:
        _record_rollback_failure_audit(g.current_user.id, None)
        logger.warning(
            "Import rollback rejected: source=%s target_batch_id=%s reason=missing_required_fields",
            source or None,
            None,
        )
        return error_response(
            400,
            "invalid_rollback_request",
            "Both source and target_batch_id are required.",
        )

    try:
        batch_uuid = UUID(str(batch_id))
    except (ValueError, TypeError):
        _record_rollback_failure_audit(g.current_user.id, None)
        logger.warning(
            "Import rollback rejected: source=%s target_batch_id=%s reason=invalid_batch_id",
            source or None,
            None,
        )
        return error_response(
            400,
            "invalid_batch_id",
            "Target batch id must be a valid UUID.",
        )

    target_batch = db.session.get(ImportBatch, batch_uuid)
    if not target_batch:
        _record_rollback_failure_audit(g.current_user.id, batch_uuid)
        logger.warning(
            "Import rollback rejected: source=%s target_batch_id=%s reason=batch_not_found",
            source or None,
            batch_uuid.hex,
        )
        return error_response(404, "not_found", "Batch not found.")

    try:
        result = rollback_source_to_batch(source, target_batch.id)
        record_audit(
            g.current_user.id,
            ACTION_IMPORT_ROLLBACK,
            ENTITY_IMPORT_BATCH,
            target_batch.id.hex,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        _record_rollback_failure_audit(g.current_user.id, batch_uuid)
        logger.warning(
            "Import rollback rejected: source=%s target_batch_id=%s reason=%s",
            source or None,
            batch_uuid.hex,
            str(exc),
        )
        return error_response(
            400,
            "invalid_rollback_target",
            str(exc),
        )
    except Exception:
        db.session.rollback()
        error_id = str(uuid.uuid4())
        _record_rollback_failure_audit(g.current_user.id, batch_uuid)
        logger.exception("Import rollback failed [%s]", error_id)
        return error_response(
            500,
            "internal_error",
            "An unexpected error occurred",
            error_id=error_id,
        )

    return (
        jsonify(
            {
                "status": "rolled_back",
                "source": result.source,
                "target_batch_id": result.target_batch_id,
                "previous_active_batch_ids": result.previous_active_batch_ids,
                "activated_counts": result.activated_counts,
            }
        ),
        200,
    )


@admin_bp.post("/uploads/contractors-2")
@require_staff
def upload_contractors_two():
    file = request.files.get("file")
    if not file:
        return error_response(
            400,
            "file_required",
            "Multipart file field 'file' is required.",
        )

    try:
        # Save file to temporary location
        file_ext = os.path.splitext(file.filename)[1] or '.xlsx'
        temp_file = NamedTemporaryFile(
            delete=False,
            suffix=file_ext,
            dir=str(UPLOADS_DIR)
        )
        file.save(temp_file.name)
        file_path = Path(temp_file.name)

        # Create batch
        batch = ImportBatch(
            name=f"contractors-2-{_utc_timestamp_name()}",
            source="contractors-2",
            status=STATUS_PENDING,
            uploaded_by=g.current_user.username,
        )
        db.session.add(batch)
        db.session.flush()
        record_audit(g.current_user.id, ACTION_IMPORT_UPLOAD, ENTITY_IMPORT_BATCH, batch.id.hex)
        db.session.commit()

        # Start background processing
        thread = threading.Thread(
            target=_process_file_background,
            args=(batch.id, file_path, "contractors-2"),
            daemon=False
        )
        thread.start()

        # Return immediately with 202 Accepted
        return (
            jsonify(
                {
                    "batch_id": batch.id.hex,
                    "status": STATUS_PENDING,
                    "message": "File uploaded successfully. Processing in background.",
                }
            ),
            202,
        )
    except Exception:
        db.session.rollback()
        error_id = str(uuid.uuid4())
        logger.exception("contractors-2 upload failed [%s]", error_id)
        return error_response(
            500,
            "internal_error",
            "An unexpected error occurred",
            error_id=error_id,
        )


@admin_bp.get("/uploads/<batch_id>")
@require_staff
def batch_status(batch_id: str):
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        return error_response(
            400,
            "invalid_batch_id",
            "Batch id must be a valid UUID.",
        )

    batch = ImportBatch.query.get(batch_uuid)
    if not batch:
        return error_response(404, "not_found", "Batch not found.")

    errors = [
        {
            "source_file": error.source_file,
            "row_index": error.row_index,
            "message": error.message,
            "payload": error.payload,
        }
        for error in ImportError.query.filter_by(batch_id=batch.id).order_by(ImportError.row_index).all()
    ]

    return (
        jsonify(
            {
                "batch": {
                    "id": batch.id.hex,
                    "status": batch.status,
                    "uploaded_by": batch.uploaded_by,
                    "notes": batch.notes,
                },
                "errors": errors,
            }
        ),
        200,
    )


@admin_bp.get("/templates/codtafsiltamin")
@require_staff
def download_codtafsiltamin_template():
    template_file = generate_codtafsiltamin_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="codtafsiltamin_template.xlsx",
    )


@admin_bp.get("/templates/contractors-1")
@require_staff
def download_contractors_one_template():
    template_file = generate_contractors_one_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contractors-1_template.xlsx",
    )


@admin_bp.get("/templates/contractors-2")
@require_staff
def download_contractors_two_template():
    template_file = generate_contractors_two_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contractors-2_template.xlsx",
    )


@admin_bp.get("/contractors")
@require_staff
def list_contractors():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = active_query(Contractor)

    if search:
        query = query.filter(
            db.or_(
                Contractor.name.ilike(f"%{search}%"),
                Contractor.detail_code.ilike(f"%{search}%"),
                Contractor.supplier_code.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(Contractor.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return (
        jsonify(
            {
                "items": [
                    {
                        "id": c.id.hex,
                        "detail_code": c.detail_code,
                        "supplier_code": c.supplier_code,
                        "name": c.name,
                        "status": c.status,
                        "type": c.type,
                    }
                    for c in pagination.items
                ],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@admin_bp.post("/contractors/<contractor_id>/create-user")
@require_staff
def create_contractor_user(contractor_id: str):
    """
    ایجاد کاربر برای یک contractor بر اساس detail_code و supplier_code.
    Username و password بر اساس کدها تولید می‌شوند و غیرقابل تغییر هستند.
    """
    try:
        contractor_uuid = uuid.UUID(contractor_id)
    except ValueError:
        return error_response(
            400,
            "invalid_contractor_id",
            "Contractor id must be a valid UUID.",
        )

    contractor = active_query(Contractor).filter_by(id=contractor_uuid).first()
    if not contractor:
        return error_response(404, "contractor_not_found", "Contractor not found.")

    # بررسی اینکه آیا کاربری از قبل وجود دارد
    existing_user = User.query.filter_by(contractor_id=contractor.id).first()
    if existing_user:
        return error_response(
            400,
            "user_exists",
            "کاربری برای این پیمانکار از قبل وجود دارد.",
            extra={"username": existing_user.username},
        )

    # تولید username و password
    username = generate_username(contractor)
    password = generate_password(contractor)

    # بررسی اینکه username تکراری نباشد
    if User.query.filter_by(username=username).first():
        return error_response(
            400,
            "username_exists",
            f"نام کاربری '{username}' از قبل وجود دارد.",
        )

    # ایجاد user
    user = User(
        username=username,
        contractor_id=contractor.id,
        must_change_password=False,
        role="contractor",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "username": username,
        "password": password,  # فقط یکبار نمایش می‌شود
        "must_change_password": False,
        "contractor": {
            "id": contractor.id.hex,
            "name": contractor.name,
            "detail_code": contractor.detail_code,
            "supplier_code": contractor.supplier_code,
        },
        "message": "کاربر با موفقیت ایجاد شد. لطفاً اطلاعات ورود را به پیمانکار تحویل دهید."
    }), 201


@admin_bp.get("/invoice-summaries")
@require_staff
def list_invoice_summaries():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = active_query(InvoiceSummary)

    if search:
        # Join with Contractor for search
        query = query.outerjoin(Contractor, InvoiceSummary.contractor_id == Contractor.id)
        query = query.filter(
            db.or_(
                InvoiceSummary.cover_number.ilike(f"%{search}%"),
                InvoiceSummary.automation_number.ilike(f"%{search}%"),
                Contractor.name.ilike(f"%{search}%"),
                InvoiceSummary.client_name.ilike(f"%{search}%"),
                InvoiceSummary.business_owner.ilike(f"%{search}%"),
                InvoiceSummary.detail_code.ilike(f"%{search}%"),
                InvoiceSummary.supplier_code.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(InvoiceSummary.invoice_date.desc(), InvoiceSummary.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return (
        jsonify(
            {
                "items": [
                    {
                        "id": s.id.hex,
                        "cover_number": s.cover_number,
                        "automation_number": s.automation_number,
                        "invoice_date": s.invoice_date.isoformat() if s.invoice_date else None,
                        "invoice_status": s.invoice_status,
                        "gross_amount": float(s.gross_amount) if s.gross_amount else 0,
                        "net_amount": float(s.net_amount) if s.net_amount else 0,
                        "supplier_name": s.contractor.name if s.contractor else (s.raw_payload.get("نام تامین کننده") if s.raw_payload and isinstance(s.raw_payload, dict) else None),
                        "detail_code": s.detail_code,
                        "supplier_code": s.supplier_code,
                        "business_owner": s.business_owner,
                        "client_name": s.client_name,
                    }
                    for s in pagination.items
                ],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@admin_bp.get("/invoice-details")
@require_staff
def list_invoice_details():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = active_query(InvoiceDetail)

    if search:
        query = query.filter(
            db.or_(
                InvoiceDetail.cover_number.ilike(f"%{search}%"),
                InvoiceDetail.invoice_no.ilike(f"%{search}%"),
                InvoiceDetail.supplier_name.ilike(f"%{search}%"),
                InvoiceDetail.item_title.ilike(f"%{search}%"),
                InvoiceDetail.description.ilike(f"%{search}%"),
                InvoiceDetail.reference.ilike(f"%{search}%"),
                InvoiceDetail.detail_code.ilike(f"%{search}%"),
                InvoiceDetail.supplier_code.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(InvoiceDetail.invoice_date.desc(), InvoiceDetail.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return (
        jsonify(
            {
                "items": [
                    {
                        "id": d.id.hex,
                        "cover_number": d.cover_number,
                        "invoice_no": d.invoice_no,
                        "invoice_date": d.invoice_date.isoformat() if d.invoice_date else None,
                        "status": d.status,
                        "item_title": d.item_title,
                        "gross_amount": float(d.gross_amount) if d.gross_amount else 0,
                        "supplier_name": d.supplier_name,
                        "unit_code": d.unit_code,
                        "reference": d.reference,
                        "description": d.description,
                        "detail_code": d.detail_code,
                        "supplier_code": d.supplier_code,
                    }
                    for d in pagination.items
                ],
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            }
        ),
        200,
    )
