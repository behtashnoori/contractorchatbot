"""Check expert user status."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.app.models import User, Contractor

app = create_app()
with app.app_context():
    expert = User.query.filter_by(username='expert').first()
    print('Expert exists:', expert is not None)
    if expert:
        print('Contractor ID:', expert.contractor_id)
        print('Contractor exists:', expert.contractor is not None)
        if expert.contractor:
            print('Contractor detail_code:', expert.contractor.detail_code)
            print('Contractor status:', expert.contractor.status)
    
    admin_contractor = Contractor.query.filter_by(detail_code='CNT-ADMIN').first()
    print('CNT-ADMIN exists:', admin_contractor is not None)
    if admin_contractor:
        print('CNT-ADMIN status:', admin_contractor.status)

