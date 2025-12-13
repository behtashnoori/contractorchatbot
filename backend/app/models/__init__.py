from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Index

from ..extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class BaseModel(db.Model):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:  # type: ignore[override]
        return cls.__name__.lower()

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class Contractor(TimestampMixin, BaseModel):
    detail_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    supplier_code = db.Column(db.String(32), index=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    type = db.Column(db.String(64))
    relationship_start = db.Column(db.Date)
    raw_payload = db.Column(db.JSON)

    users = db.relationship("User", back_populates="contractor", lazy="dynamic")
    invoice_summaries = db.relationship(
        "InvoiceSummary", back_populates="contractor", lazy="dynamic"
    )
    invoice_details = db.relationship(
        "InvoiceDetail", back_populates="contractor", lazy="dynamic"
    )


class InvoiceSummary(TimestampMixin, BaseModel):
    contractor_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("contractor.id"), nullable=True
    )
    detail_code = db.Column(db.String(32), index=True)
    supplier_code = db.Column(db.String(32), index=True)
    automation_number = db.Column(db.String(64), index=True)
    invoice_created_at = db.Column(db.Date)
    delivered_to_accounting_at = db.Column(db.Date)
    delivered_to_supervisor_at = db.Column(db.Date)
    invoice_date = db.Column(db.Date)
    cover_number = db.Column(db.String(64), index=True)
    business_owner = db.Column(db.String(255))
    cost_subject = db.Column(db.String(255))
    gross_amount = db.Column(db.Numeric(18, 2))
    net_amount = db.Column(db.Numeric(18, 2))
    time_span = db.Column(db.String(128))
    invoice_status = db.Column(db.String(64))
    notes = db.Column(db.Text)
    contractor_invoice_no = db.Column(db.String(128))
    permit_number = db.Column(db.String(128))
    permit_type = db.Column(db.String(128))
    client_contract_number = db.Column(db.String(128))
    client_name = db.Column(db.String(255))
    raw_payload = db.Column(db.JSON)
    last_update_batch_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("importbatch.id"), nullable=True
    )

    contractor = db.relationship("Contractor", back_populates="invoice_summaries")
    batch = db.relationship("ImportBatch", back_populates="invoice_summaries")
    details = db.relationship(
        "InvoiceDetail",
        primaryjoin="InvoiceSummary.cover_number==foreign(InvoiceDetail.cover_number)",
        viewonly=True,
    )
    
    __table_args__ = (
        Index('idx_invoice_summary_detail_supplier', 'detail_code', 'supplier_code'),
        Index('idx_invoice_summary_cover_detail', 'cover_number', 'detail_code'),
        Index('idx_invoice_summary_created_status', 'invoice_created_at', 'invoice_status'),
    )


class InvoiceDetail(TimestampMixin, BaseModel):
    contractor_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("contractor.id"), nullable=True
    )
    detail_code = db.Column(db.String(32), index=True)
    supplier_code = db.Column(db.String(32), index=True)
    invoice_no = db.Column(db.String(64), index=True)
    invoice_date = db.Column(db.Date)
    unit_code = db.Column(db.String(128))
    supplier_name = db.Column(db.String(255))
    status = db.Column(db.String(64))
    item_title = db.Column(db.String(255))
    gross_amount = db.Column(db.Numeric(18, 2))
    reference = db.Column(db.String(255))
    description = db.Column(db.Text)
    cover_number = db.Column(db.String(64), index=True)
    raw_payload = db.Column(db.JSON)
    last_update_batch_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("importbatch.id"), nullable=True
    )

    contractor = db.relationship("Contractor", back_populates="invoice_details")
    batch = db.relationship("ImportBatch", back_populates="invoice_details")
    
    __table_args__ = (
        Index('idx_invoice_detail_supplier_cover', 'supplier_code', 'cover_number'),
        Index('idx_invoice_detail_cover_detail', 'cover_number', 'detail_code'),
    )


class User(TimestampMixin, BaseModel):
    username = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    must_change_password = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime)
    contractor_id = db.Column(UUID(as_uuid=True), db.ForeignKey("contractor.id"))

    contractor = db.relationship("Contractor", back_populates="users")

    def set_password(self, password: str) -> None:
        from ..extensions import bcrypt

        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        from ..extensions import bcrypt

        return bcrypt.check_password_hash(self.password_hash, password)


class ImportBatch(TimestampMixin, BaseModel):
    name = db.Column(db.String(255))
    source = db.Column(db.String(64))
    status = db.Column(db.String(32), nullable=False, default="pending")
    uploaded_by = db.Column(db.String(128))
    notes = db.Column(db.Text)
    # Progress tracking fields
    total_rows = db.Column(db.Integer, default=0)
    rows_processed = db.Column(db.Integer, default=0)
    progress_percentage = db.Column(db.Float, default=0.0)
    # Import result fields
    inserted_count = db.Column(db.Integer, default=0)
    updated_count = db.Column(db.Integer, default=0)
    errors_count = db.Column(db.Integer, default=0)

    invoice_summaries = db.relationship("InvoiceSummary", back_populates="batch")
    invoice_details = db.relationship("InvoiceDetail", back_populates="batch")
    errors = db.relationship("ImportError", back_populates="batch")
    
    def update_progress(self, processed: int, total: int):
        """Update progress tracking"""
        self.rows_processed = processed
        self.total_rows = total
        self.progress_percentage = (processed / total * 100) if total > 0 else 0.0
        db.session.flush()  # Flush first to ensure values are set
        db.session.commit()
        print(f"[ImportBatch] Progress updated: {processed}/{total} ({self.progress_percentage:.1f}%)")
    
    def update_metrics(self, inserted: int, updated: int, errors: int):
        """Update import metrics"""
        self.inserted_count = inserted
        self.updated_count = updated
        self.errors_count = errors
        db.session.commit()


class ImportError(TimestampMixin, BaseModel):
    batch_id = db.Column(UUID(as_uuid=True), db.ForeignKey("importbatch.id"))
    source_file = db.Column(db.String(128))
    row_index = db.Column(db.Integer)
    message = db.Column(db.String(255))
    payload = db.Column(db.JSON)

    batch = db.relationship("ImportBatch", back_populates="errors")

