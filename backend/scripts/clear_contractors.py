"""Script to clear all contractors and related import data."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app import create_app
from backend.app.extensions import db
from backend.app.models import Contractor, ImportBatch, ImportError, User

def main() -> None:
    app = create_app()
    with app.app_context():
        print("Clearing contractors and import data...")
        
        # First, unlink users from contractors (set contractor_id to NULL)
        user_count = User.query.filter(User.contractor_id.isnot(None)).update({User.contractor_id: None})
        db.session.commit()
        print(f"Unlinked {user_count} users from contractors")
        
        # Delete import errors first (foreign key constraint)
        error_count = ImportError.query.delete()
        db.session.commit()
        print(f"Deleted {error_count} import errors")
        
        # Delete import batches
        batch_count = ImportBatch.query.delete()
        db.session.commit()
        print(f"Deleted {batch_count} import batches")
        
        # Delete contractors
        contractor_count = Contractor.query.delete()
        db.session.commit()
        print(f"Deleted {contractor_count} contractors")
        
        # Verify
        remaining = Contractor.query.count()
        print(f"Remaining contractors: {remaining}")
        print("Database cleared successfully!")

if __name__ == "__main__":
    main()
