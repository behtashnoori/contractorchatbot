from __future__ import annotations

import logging
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from uuid import UUID

from ..extensions import db
from ..models import Contractor, ImportBatch, ImportError, User, InvoiceSummary, InvoiceDetail
from ..services.codtafsiltamin_importer import CodTafsiltaminImporter
from ..utils.auth_utils import generate_username, generate_password, resolve_user_id, user_has_staff_access
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
            
            batch.status = "processing"
            db.session.commit()
            
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
                
                batch.status = "completed_with_errors" if result.errors else "completed"

                # Update metrics
                batch.update_metrics(result.inserted, result.updated, result.errors)
                logger.info(
                    "Completed %s import: inserted=%s updated=%s errors=%s status=%s",
                    source,
                    result.inserted,
                    result.updated,
                    result.errors,
                    batch.status,
                )
                
        except ValueError as exc:
            logger.exception("ValueError in %s import", source)
            db.session.refresh(batch)
            batch.status = "failed"
            batch.notes = str(exc)
            db.session.commit()
        except Exception as exc:
            logger.exception("Exception in %s import", source)
            db.session.rollback()
            db.session.refresh(batch)
            batch.status = "failed"
            batch.notes = str(exc)
            db.session.commit()
        finally:
            # Clean up temporary file
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass


def _get_current_user():
    """Get current user from JWT identity, handling UUID conversion."""
    identity = get_jwt_identity()
    uid = resolve_user_id(identity)
    if not uid:
        return None
    return db.session.get(User, uid)


@admin_bp.post("/uploads")
@jwt_required()
def upload_batch():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    files = request.files
    if not files:
        return jsonify({"error": "no_files"}), 400

    # TODO: integrate with importer service
    batch = ImportBatch(name="manual-upload", source="manual", status="pending")
    batch.uploaded_by = current_user.username if current_user else None

    from ..extensions import db

    db.session.add(batch)
    db.session.commit()

    return jsonify({"batch_id": batch.id.hex, "status": batch.status}), 202


@admin_bp.post("/uploads/codtafsiltamin")
@jwt_required()
def upload_codtafsiltamin():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file_required"}), 400

    batch = ImportBatch(
        name=f"codtafsiltamin-{datetime.utcnow():%Y%m%d%H%M%S}",
        source="codtafsiltamin",
        status="processing",
        uploaded_by=current_user.username if current_user else None,
    )
    db.session.add(batch)
    db.session.flush()

    importer = CodTafsiltaminImporter(batch)
    try:
        result = importer.run(file)
    except ValueError as exc:
        batch.status = "failed"
        db.session.rollback()
        db.session.commit()
        logger.exception("ValueError in codtafsiltamin upload")
        return jsonify({"error": "invalid_file", "message": str(exc)}), 400
    except Exception as exc:
        batch.status = "failed"
        db.session.rollback()
        db.session.commit()
        logger.exception("Exception in codtafsiltamin upload")
        return jsonify({"error": "processing_failed", "message": str(exc)}), 500

    batch.status = "completed_with_errors" if result.errors else "completed"
    db.session.commit()

    # Count total unique contractors in database
    total_contractors = Contractor.query.count()

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
@jwt_required()
def upload_contractors_one():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file_required"}), 400

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
            name=f"contractors-1-{datetime.utcnow():%Y%m%d%H%M%S}",
            source="contractors-1",
            status="queued",
            uploaded_by=current_user.username if current_user else None,
        )
        db.session.add(batch)
        db.session.flush()
        db.session.commit()

        # Start background processing
        thread = threading.Thread(
            target=_process_file_background,
            args=(batch.id, file_path, "contractors-1"),
            daemon=True
        )
        thread.start()

        # Return immediately with 202 Accepted
        return (
            jsonify(
                {
                    "batch_id": batch.id.hex,
                    "status": "queued",
                    "message": "File uploaded successfully. Processing in background.",
                }
            ),
            202,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("contractors-1 upload failed")
        return jsonify({"error": "processing_failed", "message": str(exc)}), 500


@admin_bp.get("/uploads/<batch_id>/progress")
@jwt_required()
def get_upload_progress(batch_id):
    """Get progress of an upload batch"""
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403
    
    try:
        batch_uuid = UUID(batch_id) if isinstance(batch_id, str) else batch_id
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_batch_id"}), 400
    
    batch = ImportBatch.query.get(batch_uuid)
    if not batch:
        return jsonify({"error": "not_found"}), 404
    
    # Get metrics - use stored values if available, otherwise calculate
    # Always return metrics, even during processing
    metrics = {
        "inserted": batch.inserted_count or 0,
        "updated": batch.updated_count or 0,
        "errors": batch.errors_count or 0,
    }
    
    # If metrics are zero but batch is completed, try to calculate from database
    if batch.status in ("completed", "completed_with_errors", "failed"):
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
        "progress": {
            "percentage": batch.progress_percentage or 0.0,
            "processed": batch.rows_processed or 0,
            "total": batch.total_rows or 0,
        },
        "metrics": metrics,
    }), 200


@admin_bp.post("/uploads/contractors-2")
@jwt_required()
def upload_contractors_two():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file_required"}), 400

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
            name=f"contractors-2-{datetime.utcnow():%Y%m%d%H%M%S}",
            source="contractors-2",
            status="queued",
            uploaded_by=current_user.username if current_user else None,
        )
        db.session.add(batch)
        db.session.flush()
        db.session.commit()

        # Start background processing
        thread = threading.Thread(
            target=_process_file_background,
            args=(batch.id, file_path, "contractors-2"),
            daemon=True
        )
        thread.start()

        # Return immediately with 202 Accepted
        return (
            jsonify(
                {
                    "batch_id": batch.id.hex,
                    "status": "queued",
                    "message": "File uploaded successfully. Processing in background.",
                }
            ),
            202,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception("contractors-2 upload failed")
        return jsonify({"error": "processing_failed", "message": str(exc)}), 500


@admin_bp.get("/uploads/<batch_id>")
@jwt_required()
def batch_status(batch_id: str):
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        return jsonify({"error": "invalid_batch_id"}), 400

    batch = ImportBatch.query.get(batch_uuid)
    if not batch:
        return jsonify({"error": "not_found"}), 404

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
@jwt_required()
def download_codtafsiltamin_template():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    template_file = generate_codtafsiltamin_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="codtafsiltamin_template.xlsx",
    )


@admin_bp.get("/templates/contractors-1")
@jwt_required()
def download_contractors_one_template():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    template_file = generate_contractors_one_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contractors-1_template.xlsx",
    )


@admin_bp.get("/templates/contractors-2")
@jwt_required()
def download_contractors_two_template():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    template_file = generate_contractors_two_template()
    return send_file(
        template_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contractors-2_template.xlsx",
    )


@admin_bp.get("/contractors")
@jwt_required()
def list_contractors():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = Contractor.query

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
@jwt_required()
def create_contractor_user(contractor_id: str):
    """
    ایجاد کاربر برای یک contractor بر اساس detail_code و supplier_code.
    Username و password بر اساس کدها تولید می‌شوند و غیرقابل تغییر هستند.
    """
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    try:
        contractor_uuid = uuid.UUID(contractor_id)
    except ValueError:
        return jsonify({"error": "invalid_contractor_id"}), 400

    contractor = Contractor.query.get(contractor_uuid)
    if not contractor:
        return jsonify({"error": "contractor_not_found"}), 404

    # بررسی اینکه آیا کاربری از قبل وجود دارد
    existing_user = User.query.filter_by(contractor_id=contractor.id).first()
    if existing_user:
        return jsonify({
            "error": "user_exists",
            "username": existing_user.username,
            "message": "کاربری برای این پیمانکار از قبل وجود دارد."
        }), 400

    # تولید username و password
    username = generate_username(contractor)
    password = generate_password(contractor)

    # بررسی اینکه username تکراری نباشد
    if User.query.filter_by(username=username).first():
        return jsonify({
            "error": "username_exists",
            "message": f"نام کاربری '{username}' از قبل وجود دارد."
        }), 400

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
@jwt_required()
def list_invoice_summaries():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = InvoiceSummary.query

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
@jwt_required()
def list_invoice_details():
    current_user = _get_current_user()
    if not user_has_staff_access(current_user):
        return jsonify({"error": "forbidden"}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()

    query = InvoiceDetail.query

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

