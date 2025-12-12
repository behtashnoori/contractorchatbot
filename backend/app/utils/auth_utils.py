"""
Helper functions for authentication and user management.
"""


def generate_username(contractor) -> str:
    """
    تولید username از detail_code و supplier_code.
    
    فرمت: {detail_code}_{supplier_code} (lowercase, normalized)
    اگر supplier_code خالی بود: فقط detail_code
    
    Args:
        contractor: Contractor model instance
        
    Returns:
        str: Username generated from contractor codes
    """
    detail_code = (contractor.detail_code or "").strip()
    supplier_code = (contractor.supplier_code or "").strip()
    
    # Normalize detail_code: remove leading zeros, lowercase, replace spaces and dashes
    # Leading zeros are removed to match database storage (e.g., "0026968" -> "26968")
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    detail_code_normalized = detail_code_cleaned.lower().replace(' ', '').replace('-', '_')
    
    if supplier_code:
        # Normalize supplier_code
        supplier_code_normalized = supplier_code.lower().replace(' ', '').replace('-', '_')
        username = f"{detail_code_normalized}_{supplier_code_normalized}"
    else:
        username = detail_code_normalized
    
    return username


def generate_password(contractor) -> str:
    """
    تولید password از detail_code و supplier_code.
    
    فرمت: {detail_code}@{supplier_code}
    اگر supplier_code خالی بود: {detail_code}@2024
    
    Args:
        contractor: Contractor model instance
        
    Returns:
        str: Password generated from contractor codes
    """
    detail_code = (contractor.detail_code or "").strip()
    supplier_code = (contractor.supplier_code or "").strip()
    
    # Remove leading zeros from detail_code for password too (to match username)
    detail_code_cleaned = detail_code.lstrip('0') if detail_code.lstrip('0') else detail_code
    
    if supplier_code:
        password = f"{detail_code_cleaned}@{supplier_code}"
    else:
        password = f"{detail_code_cleaned}@2024"
    
    return password

