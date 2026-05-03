"""Lightweight append-only audit logging (no passwords, tokens, or filenames)."""

from __future__ import annotations

import uuid

from ..extensions import db
from ..models import AuditLog

ACTION_LOGIN = "login"
ACTION_INVOICE_VIEW = "invoice.view"
ACTION_IMPORT_UPLOAD = "import.upload"

ENTITY_USER = "user"
ENTITY_INVOICE_SUMMARY = "invoice_summary"
ENTITY_IMPORT_BATCH = "import_batch"


def record_audit(
    user_id: uuid.UUID | None,
    action: str,
    entity: str,
    entity_id: str | None = None,
) -> None:
    """Queue one audit row on the current session; caller commits."""
    db.session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
        )
    )
