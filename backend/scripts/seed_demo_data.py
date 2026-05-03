from __future__ import annotations

"""
Seed demo contractor and users for local development.

Creates:
- Contractor: detail_code='CNT-DEMO', name='پیمانکار نمونه', status='فعال'
- User (contractor): username='contractor' (password set in code; not printed)
- User (expert-like admin): username='admin1' (password set in code; not printed)
- User (expert): username='expert' (password set in code; not printed)

Usage (from project root, with venv active):

    python backend/scripts/seed_demo_data.py

If records already exist, they won't be duplicated.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models import Contractor, User


def get_or_create_contractor(detail_code: str, name: str) -> Contractor:
    contractor = Contractor.query.filter_by(detail_code=detail_code).first()
    if contractor:
        return contractor
    contractor = Contractor(
        detail_code=detail_code,
        supplier_code=detail_code,
        name=name,
        status="فعال",
        type="demo",
    )
    db.session.add(contractor)
    db.session.commit()
    return contractor


def get_or_create_user(
    username: str,
    password: str,
    contractor: Contractor,
    *,
    role: str = "contractor",
) -> User:
    user = User.query.filter_by(username=username.lower()).first()
    if user:
        # ensure contractor/status linkage remains valid
        if not user.contractor_id:
            user.contractor_id = contractor.id
            db.session.commit()
        if user.role != role:
            user.role = role
            db.session.commit()
        return user
    user = User(
        username=username.lower(),
        contractor_id=contractor.id,
        must_change_password=False,
        role=role,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def main() -> None:
    app = create_app()
    with app.app_context():
        demo_contractor = get_or_create_contractor("CNT-DEMO", "پیمانکار نمونه")
        admin_contractor = get_or_create_contractor("CNT-ADMIN", "واحد بازرگانی")

        contractor_user = get_or_create_user("contractor", "password123", demo_contractor, role="contractor")
        admin_user = get_or_create_user("admin1", "password123", admin_contractor, role="staff")
        expert_user = get_or_create_user("expert", "expert123", admin_contractor, role="staff")

        print("== Demo seed complete ==")
        print(
            f"- Users: contractor, admin1, expert (passwords are not logged; see source for dev credentials)"
        )
        print(f"- CNT-DEMO contractor: {demo_contractor.detail_code}")
        print(f"- CNT-ADMIN contractor: {admin_contractor.detail_code}")


if __name__ == "__main__":
    main()



