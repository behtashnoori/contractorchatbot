from __future__ import annotations

"""
Seed demo contractor and users for local development.

Creates:
- Contractor: detail_code='CNT-DEMO', name='پیمانکار نمونه', status='فعال'
- User (contractor): username='contractor', password='password123'
- User (expert-like admin): username='admin1', password='password123' (also linked to a contractor)
- User (expert): username='expert', password='expert123' (also linked to CNT-ADMIN contractor)

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


def get_or_create_user(username: str, password: str, contractor: Contractor) -> User:
    user = User.query.filter_by(username=username.lower()).first()
    if user:
        # ensure contractor/status linkage remains valid
        if not user.contractor_id:
            user.contractor_id = contractor.id
            db.session.commit()
        return user
    user = User(username=username.lower(), contractor_id=contractor.id, must_change_password=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def main() -> None:
    app = create_app()
    with app.app_context():
        demo_contractor = get_or_create_contractor("CNT-DEMO", "پیمانکار نمونه")
        admin_contractor = get_or_create_contractor("CNT-ADMIN", "واحد بازرگانی")

        contractor_user = get_or_create_user("contractor", "password123", demo_contractor)
        admin_user = get_or_create_user("admin1", "password123", admin_contractor)
        expert_user = get_or_create_user("expert", "expert123", admin_contractor)

        print("== Demo seed complete ==")
        print(f"- Contractor user: username=contractor  password=password123  contractor={demo_contractor.detail_code}")
        print(f"- Expert/Admin user: username=admin1  password=password123  contractor={admin_contractor.detail_code}")
        print(f"- Expert user: username=expert  password=expert123  contractor={admin_contractor.detail_code}")


if __name__ == "__main__":
    main()



