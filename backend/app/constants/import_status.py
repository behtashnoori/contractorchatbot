"""Canonical ImportBatch.status values."""

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

TERMINAL_STATUSES = frozenset({STATUS_DONE, STATUS_FAILED})
