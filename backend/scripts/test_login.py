"""Test login for expert user."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app

app = create_app()
with app.test_client() as client:
    response = client.post(
        '/auth/login',
        json={'username': 'expert', 'password': 'expert123'},
        content_type='application/json'
    )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.get_data(as_text=True)}')
