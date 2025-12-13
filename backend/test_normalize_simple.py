"""
Simple test for normalization functions without database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import only the functions we need
def normalize_username(username: str) -> str:
    username = username.strip().lower()
    
    if '_' in username:
        parts = username.split('_', 1)
        detail_code = parts[0]
        supplier_code = parts[1] if len(parts) > 1 else ''
        
        detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
        
        if supplier_code:
            supplier_code_normalized = supplier_code.replace(' ', '').replace('-', '_')
            return f"{detail_code_cleaned}_{supplier_code_normalized}"
        else:
            return detail_code_cleaned.replace(' ', '').replace('-', '_')
    else:
        detail_code_cleaned = username.lstrip('0') if username.lstrip('0') else username
        return detail_code_cleaned.replace(' ', '').replace('-', '_')

def normalize_password(password: str) -> str:
    password = password.strip()
    
    if '@' in password:
        parts = password.split('@', 1)
        detail_code = parts[0]
        supplier_code = parts[1] if len(parts) > 1 else ''
        
        detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
        
        if supplier_code:
            return f"{detail_code_cleaned}@{supplier_code}"
        else:
            return f"{detail_code_cleaned}@2024"
    else:
        return password.lstrip('0') if password.lstrip('0') else password

def generate_username_from_codes(detail_code: str, supplier_code: str = "") -> str:
    detail_code = (detail_code or "").strip()
    supplier_code = (supplier_code or "").strip()
    
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    detail_code_normalized = detail_code_cleaned.lower().replace(' ', '').replace('-', '_')
    
    if supplier_code:
        supplier_code_normalized = supplier_code.lower().replace(' ', '').replace('-', '_')
        username = f"{detail_code_normalized}_{supplier_code_normalized}"
    else:
        username = detail_code_normalized
    
    return username

def generate_password_from_codes(detail_code: str, supplier_code: str = "") -> str:
    detail_code = (detail_code or "").strip()
    supplier_code = (supplier_code or "").strip()
    
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    
    if supplier_code:
        password = f"{detail_code_cleaned}@{supplier_code}"
    else:
        password = f"{detail_code_cleaned}@2024"
    
    return password

print("=" * 60)
print("Testing Normalization Functions")
print("=" * 60)

# Test cases
test_cases = [
    ("71499", "726"),
    ("071499", "726"),
    ("71499", "0726"),
    ("071499", "0726"),
]

print("\n1. Testing username generation and normalization:")
for detail_code, supplier_code in test_cases:
    generated = generate_username_from_codes(detail_code, supplier_code)
    print(f"   detail_code='{detail_code}', supplier_code='{supplier_code}'")
    print(f"   -> Generated username: '{generated}'")
    
    # Test normalization of various input formats
    test_inputs = [
        f"{detail_code}_{supplier_code}",
        f"0{detail_code}_{supplier_code}",
        f"{detail_code}-{supplier_code}",
    ]
    for test_input in test_inputs:
        normalized = normalize_username(test_input)
        match = "OK" if normalized == generated else "FAIL"
        print(f"   {match} Input: '{test_input}' -> Normalized: '{normalized}'")

print("\n2. Testing password generation and normalization:")
for detail_code, supplier_code in test_cases:
    generated = generate_password_from_codes(detail_code, supplier_code)
    print(f"   detail_code='{detail_code}', supplier_code='{supplier_code}'")
    print(f"   -> Generated password: '{generated}'")
    
    # Test normalization of various input formats
    test_inputs = [
        f"{detail_code}@{supplier_code}",
        f"0{detail_code}@{supplier_code}",
        f"{detail_code}@0{supplier_code}",
    ]
    for test_input in test_inputs:
        normalized = normalize_password(test_input)
        match = "OK" if normalized == generated else "FAIL"
        print(f"   {match} Input: '{test_input}' -> Normalized: '{normalized}'")

print("\n" + "=" * 60)
print("Testing specific case: 71499_726 / 71499@726")
print("=" * 60)

# Specific test case from user
user_input_username = "71499_726"
user_input_password = "71499@726"

normalized_username = normalize_username(user_input_username)
normalized_password = normalize_password(user_input_password)

print(f"\nUser input username: '{user_input_username}'")
print(f"Normalized username: '{normalized_username}'")

print(f"\nUser input password: '{user_input_password}'")
print(f"Normalized password: '{normalized_password}'")

# Check what would be generated for detail_code=71499, supplier_code=726
expected_username = generate_username_from_codes("71499", "726")
expected_password = generate_password_from_codes("71499", "726")

print(f"\nExpected username (from codes 71499, 726): '{expected_username}'")
print(f"Expected password (from codes 71499, 726): '{expected_password}'")

print(f"\nUsername match: {'OK' if normalized_username == expected_username else 'FAIL'}")
print(f"Password match: {'OK' if normalized_password == expected_password else 'FAIL'}")

# Also test with leading zeros
print("\n" + "=" * 60)
print("Testing with leading zeros in detail_code")
print("=" * 60)

expected_username_leading = generate_username_from_codes("071499", "726")
expected_password_leading = generate_password_from_codes("071499", "726")

print(f"Expected username (from codes 071499, 726): '{expected_username_leading}'")
print(f"Expected password (from codes 071499, 726): '{expected_password_leading}'")

print(f"\nUsername match (with leading zero): {'OK' if normalized_username == expected_username_leading else 'FAIL'}")
print(f"Password match (with leading zero): {'OK' if normalized_password == expected_password_leading else 'FAIL'}")

