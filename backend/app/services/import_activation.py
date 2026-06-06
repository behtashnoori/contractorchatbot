from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from ..constants.import_status import STATUS_DONE
from ..extensions import db
from ..models import Contractor, ImportBatch, InvoiceDetail, InvoiceSummary, User, utc_now


ACTIVE_MODELS_BY_SOURCE: dict[str, tuple[Type, ...]] = {
    "codtafsiltamin": (Contractor,),
    "contractors-1": (InvoiceSummary, InvoiceDetail),
    "contractors-2": (InvoiceDetail,),
}


@dataclass(frozen=True)
class RollbackResult:
    source: str
    target_batch_id: str
    previous_active_batch_ids: list[str]
    activated_counts: dict[str, int]


def active_query(model: Type):
    return model.query.filter(model.is_active.is_(True))


def active_filter(model: Type):
    return model.is_active.is_(True)


def mark_previous_active_replaced(source: str, new_batch: ImportBatch) -> None:
    batch_ids: set = set()
    for model in ACTIVE_MODELS_BY_SOURCE[source]:
        rows = (
            db.session.query(model.last_update_batch_id)
            .filter(model.is_active.is_(True))
            .filter(model.last_update_batch_id.isnot(None))
            .distinct()
            .all()
        )
        batch_ids.update(row[0] for row in rows if row[0] and row[0] != new_batch.id)

    if not batch_ids:
        return

    ImportBatch.query.filter(ImportBatch.id.in_(batch_ids)).update(
        {ImportBatch.replaced_by_batch_id: new_batch.id},
        synchronize_session=False,
    )


def deactivate_active_rows(source: str) -> None:
    for model in ACTIVE_MODELS_BY_SOURCE[source]:
        model.query.filter(model.is_active.is_(True)).update(
            {model.is_active: False},
            synchronize_session=False,
        )


def mark_batch_published(batch: ImportBatch) -> None:
    batch.published_at = utc_now()


def _active_batch_ids_for_source(source: str) -> set:
    batch_ids: set = set()
    for model in ACTIVE_MODELS_BY_SOURCE[source]:
        rows = (
            db.session.query(model.last_update_batch_id)
            .filter(model.is_active.is_(True))
            .filter(model.last_update_batch_id.isnot(None))
            .distinct()
            .all()
        )
        batch_ids.update(row[0] for row in rows if row[0])
    return batch_ids


def _target_row_counts(source: str, target_batch: ImportBatch) -> dict[str, int]:
    return {
        model.__tablename__: model.query.filter(
            model.last_update_batch_id == target_batch.id
        ).count()
        for model in ACTIVE_MODELS_BY_SOURCE[source]
    }


def _active_contractors_by_detail_code() -> dict[str, Contractor]:
    return {
        contractor.detail_code: contractor
        for contractor in active_query(Contractor).all()
        if contractor.detail_code
    }


def _relink_users_to_target_contractors(previous_active_contractors: list[Contractor]) -> None:
    target_contractors = _active_contractors_by_detail_code()
    for previous_contractor in previous_active_contractors:
        target_contractor = target_contractors.get(previous_contractor.detail_code)
        if not target_contractor:
            continue
        User.query.filter_by(contractor_id=previous_contractor.id).update(
            {User.contractor_id: target_contractor.id},
            synchronize_session=False,
        )


def rollback_source_to_batch(source: str, batch_id) -> RollbackResult:
    """Backend-level rollback helper; caller owns authorization and commit scope."""
    if source not in ACTIVE_MODELS_BY_SOURCE:
        raise ValueError(f"Unknown import source: {source}")

    target_batch = db.session.get(ImportBatch, batch_id)
    if not target_batch or target_batch.source != source:
        raise ValueError("Rollback target batch does not exist for the requested source.")
    if target_batch.status != STATUS_DONE or target_batch.published_at is None:
        raise ValueError("Rollback target batch must be a published successful batch.")

    target_counts = _target_row_counts(source, target_batch)
    if not any(target_counts.values()):
        raise ValueError("Rollback target batch has no rows to publish.")

    previous_active_batch_ids = _active_batch_ids_for_source(source)
    previous_active_contractors: list[Contractor] = []
    if source == "codtafsiltamin":
        previous_active_contractors = active_query(Contractor).all()

    activated_counts: dict[str, int] = {}

    for model in ACTIVE_MODELS_BY_SOURCE[source]:
        model.query.filter(model.is_active.is_(True)).update(
            {model.is_active: False},
            synchronize_session=False,
        )
        activated_counts[model.__tablename__] = model.query.filter(
            model.last_update_batch_id == target_batch.id
        ).update(
            {model.is_active: True},
            synchronize_session=False,
        )

    if source == "codtafsiltamin":
        _relink_users_to_target_contractors(previous_active_contractors)

    batch_ids_to_mark_replaced = {
        batch_id
        for batch_id in previous_active_batch_ids
        if batch_id != target_batch.id
    }
    if batch_ids_to_mark_replaced:
        ImportBatch.query.filter(ImportBatch.id.in_(batch_ids_to_mark_replaced)).update(
            {ImportBatch.replaced_by_batch_id: target_batch.id},
            synchronize_session=False,
        )

    target_batch.replaced_by_batch_id = None
    target_batch.published_at = utc_now()

    return RollbackResult(
        source=source,
        target_batch_id=target_batch.id.hex,
        previous_active_batch_ids=sorted(batch_id.hex for batch_id in previous_active_batch_ids),
        activated_counts=activated_counts,
    )
