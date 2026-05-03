"""
Check if user exists in database and what format their username is stored
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db
from app.models import User, Contractor
from app.utils.auth_utils import generate_username_variants, generate_username

app = create_app()

def check_user():
    with app.app_context():
        print("=" * 60)
        print("Checking for user: 71499_726")
        print("=" * 60)
        
        # Check all username variants
        username_variants = generate_username_variants("71499_726")
        print(f"\n1. Checking {len(username_variants)} username variants:")
        found_users = []
        for variant in username_variants:
            user = User.query.filter_by(username=variant).first()
            if user:
                found_users.append((variant, user))
                print(f"   ✓ Found user with username: '{variant}'")
                if user.contractor:
                    print(f"     Contractor: detail_code='{user.contractor.detail_code}', supplier_code='{user.contractor.supplier_code}'")
                    print(f"     Expected username: '{generate_username(user.contractor)}'")
        
        if not found_users:
            print("   ✗ No user found with any variant")
        
        # Check contractor
        print(f"\n2. Checking for contractor with detail_code='71499' and supplier_code='726':")
        contractors = Contractor.query.filter(
            (Contractor.detail_code.like('%71499%')) | 
            (Contractor.detail_code.like('%071499%'))
        ).all()
        
        if contractors:
            print(f"   Found {len(contractors)} contractors:")
            for contractor in contractors:
                print(f"     - detail_code: '{contractor.detail_code}', supplier_code: '{contractor.supplier_code}'")
                print(f"       Expected username: '{generate_username(contractor)}'")
                
                # Check if user exists for this contractor
                user = User.query.filter_by(contractor_id=contractor.id).first()
                if user:
                    print(f"       ✓ User exists: username='{user.username}'")
                else:
                    print(f"       ✗ No user exists for this contractor")
        else:
            print("   ✗ No contractor found")
        
        # Check for any user with similar detail_code
        print(f"\n3. Checking for any user with '71499' or '726' in username:")
        similar_users = User.query.filter(
            (User.username.like('%71499%')) | 
            (User.username.like('%726%'))
        ).limit(10).all()
        
        if similar_users:
            print(f"   Found {len(similar_users)} similar users:")
            for user in similar_users:
                print(f"     - username: '{user.username}'")
                if user.contractor:
                    print(f"       contractor: detail_code='{user.contractor.detail_code}', supplier_code='{user.contractor.supplier_code}'")
        else:
            print("   ✗ No similar users found")
        
        # Check for contractor 70583_100 (the one that works)
        print(f"\n4. Checking for working user: 70583_100")
        working_variants = generate_username_variants("70583_100")
        for variant in working_variants:
            user = User.query.filter_by(username=variant).first()
            if user:
                print(f"   ✓ Found working user with username: '{variant}'")
                if user.contractor:
                    print(f"     Contractor: detail_code='{user.contractor.detail_code}', supplier_code='{user.contractor.supplier_code}'")
                    print(f"     Expected username: '{generate_username(user.contractor)}'")
                break

if __name__ == "__main__":
    check_user()

