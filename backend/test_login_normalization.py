"""
Test script for login normalization
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db
from app.models import User, Contractor
from app.utils.auth_utils import normalize_username, normalize_password, generate_username, generate_password

app = create_app()

def test_normalization():
    """Test username and password normalization"""
    print("=" * 60)
    print("Testing Normalization Functions")
    print("=" * 60)
    
    # Test username normalization
    test_cases_username = [
        "71499_726",
        "071499_726",
        "71499-726",
        "071499-726",
        "71499 726",
    ]
    
    print("\n1. Testing normalize_username:")
    for test_input in test_cases_username:
        normalized = normalize_username(test_input)
        print(f"   Input: '{test_input}' -> Normalized: '{normalized}'")
    
    # Test password normalization
    test_cases_password = [
        "71499@726",
        "071499@726",
        "71499@0726",
    ]
    
    print("\n2. Testing normalize_password:")
    for test_input in test_cases_password:
        normalized = normalize_password(test_input)
        print(f"   Input: '{test_input}' -> Normalized: '{normalized}'")
    
    print("\n" + "=" * 60)
    print("Checking Database")
    print("=" * 60)
    
    with app.app_context():
        # Search for users with similar usernames
        search_terms = ["71499", "071499"]
        for term in search_terms:
            users = User.query.filter(User.username.like(f"%{term}%")).all()
            if users:
                print(f"\nUsers found with '{term}' in username:")
                for user in users:
                    print(f"  - Username: '{user.username}'")
                    if user.contractor:
                        print(f"    Contractor: {user.contractor.detail_code} / {user.contractor.supplier_code}")
                        print(f"    Generated username would be: '{generate_username(user.contractor)}'")
                        print(f"    Generated password would be: '{generate_password(user.contractor)}'")
                    else:
                        print(f"    No contractor linked")
        
        # Try to find user with normalized username
        normalized_test = normalize_username("71499_726")
        print(f"\n3. Searching for user with normalized username: '{normalized_test}'")
        user = User.query.filter_by(username=normalized_test).first()
        if user:
            print(f"   ✓ User found: '{user.username}'")
            if user.contractor:
                print(f"   Contractor detail_code: {user.contractor.detail_code}")
                print(f"   Contractor supplier_code: {user.contractor.supplier_code}")
                
                # Test password
                test_password = "71499@726"
                normalized_pwd = normalize_password(test_password)
                print(f"\n4. Testing password:")
                print(f"   Input password: '{test_password}'")
                print(f"   Normalized password: '{normalized_pwd}'")
                print(f"   Password check result: {user.check_password(normalized_pwd)}")
                
                # Also test with original password format
                expected_password = generate_password(user.contractor)
                print(f"   Expected password (from contractor): '{expected_password}'")
                print(f"   Password check with expected: {user.check_password(expected_password)}")
        else:
            print(f"   ✗ User not found with username: '{normalized_test}'")
            
            # Try to find contractor
            contractors = Contractor.query.filter(
                (Contractor.detail_code.like(f"%71499%")) | 
                (Contractor.detail_code.like(f"%071499%"))
            ).all()
            if contractors:
                print(f"\n   Found {len(contractors)} contractors with similar detail_code:")
                for contractor in contractors:
                    print(f"     - detail_code: '{contractor.detail_code}', supplier_code: '{contractor.supplier_code}'")
                    print(f"       Would generate username: '{generate_username(contractor)}'")
                    print(f"       Would generate password: '{generate_password(contractor)}'")

if __name__ == "__main__":
    test_normalization()

