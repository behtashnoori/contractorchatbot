#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اسکریپت تست برای ایجاد کاربر و تست login
"""
import requests
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BASE_URL = "http://localhost:3855"
ADMIN_USERNAME = "admin1"  # یا username admin شما
ADMIN_PASSWORD = "password123"  # یا password admin شما

# Contractor info
DETAIL_CODE = "0026968"
SUPPLIER_CODE = "732"

def generate_username(detail_code, supplier_code):
    """تولید username"""
    detail_code = (detail_code or "").strip()
    supplier_code = (supplier_code or "").strip()
    
    detail_code_normalized = detail_code.lower().replace(' ', '').replace('-', '_')
    
    if supplier_code:
        supplier_code_normalized = supplier_code.lower().replace(' ', '').replace('-', '_')
        username = f"{detail_code_normalized}_{supplier_code_normalized}"
    else:
        username = detail_code_normalized
    
    return username

def generate_password(detail_code, supplier_code):
    """تولید password"""
    detail_code = (detail_code or "").strip()
    supplier_code = (supplier_code or "").strip()
    
    if supplier_code:
        password = f"{detail_code}@{supplier_code}"
    else:
        password = f"{detail_code}@2024"
    
    return password

def main():
    print("=" * 60)
    print("تست ایجاد کاربر و Login")
    print("=" * 60)
    
    # محاسبه username و password
    username = generate_username(DETAIL_CODE, SUPPLIER_CODE)
    password = generate_password(DETAIL_CODE, SUPPLIER_CODE)
    
    print(f"\n📝 اطلاعات تولید شده:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    
    # Step 1: Login as admin
    print(f"\n🔐 Step 1: ورود به عنوان Admin...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"❌ خطا در ورود admin: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        admin_token = login_response.json()["access_token"]
        print("✅ ورود admin موفق بود")
        
    except requests.exceptions.ConnectionError:
        print("❌ نمی‌توان به سرور متصل شد. لطفاً مطمئن شوید سرور در حال اجرا است.")
        return
    except Exception as e:
        print(f"❌ خطا: {e}")
        return
    
    # Step 2: Find contractor
    print(f"\n🔍 Step 2: جستجوی Contractor...")
    try:
        # First try searching by detail_code
        contractors_response = requests.get(
            f"{BASE_URL}/admin/contractors",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"search": DETAIL_CODE},
            timeout=5
        )
        
        if contractors_response.status_code != 200:
            print(f"❌ خطا در دریافت لیست contractors: {contractors_response.status_code}")
            return
        
        contractors = contractors_response.json()["items"]
        contractor = None
        
        # Try exact match first
        for c in contractors:
            if c["detail_code"] == DETAIL_CODE or c["detail_code"] == DETAIL_CODE.lstrip('0'):
                contractor = c
                break
        
        # If not found, try by supplier_code
        if not contractor:
            contractors_response2 = requests.get(
                f"{BASE_URL}/admin/contractors",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"search": SUPPLIER_CODE},
                timeout=5
            )
            if contractors_response2.status_code == 200:
                contractors2 = contractors_response2.json()["items"]
                for c in contractors2:
                    if c.get("supplier_code") == SUPPLIER_CODE:
                        contractor = c
                        print(f"⚠️  Contractor با supplier_code '{SUPPLIER_CODE}' یافت شد:")
                        print(f"   Detail Code: {c['detail_code']} (ممکن است با '{DETAIL_CODE}' متفاوت باشد)")
                        break
        
        if not contractor:
            print(f"❌ Contractor با کد تفصیلی '{DETAIL_CODE}' یافت نشد!")
            
            # Get all contractors to see what's available
            all_contractors_response = requests.get(
                f"{BASE_URL}/admin/contractors",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"per_page": 50},
                timeout=5
            )
            if all_contractors_response.status_code == 200:
                all_contractors = all_contractors_response.json()["items"]
                print(f"\n📋 Contractors موجود ({len(all_contractors)} مورد):")
                for c in all_contractors[:20]:
                    print(f"  - {c['detail_code']} | {c['supplier_code']} | {c['name']}")
                
                # Check if maybe supplier_code matches
                matching_supplier = [c for c in all_contractors if c.get('supplier_code') == SUPPLIER_CODE]
                if matching_supplier:
                    print(f"\n⚠️  Contractors با کد تامین‌کننده '{SUPPLIER_CODE}':")
                    for c in matching_supplier:
                        print(f"  - {c['detail_code']} | {c['supplier_code']} | {c['name']}")
            return
        
        print(f"✅ Contractor یافت شد:")
        print(f"  ID: {contractor['id']}")
        print(f"  نام: {contractor['name']}")
        print(f"  کد تفصیلی: {contractor['detail_code']}")
        print(f"  کد تامین‌کننده: {contractor['supplier_code']}")
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return
    
    # Step 3: Create user
    print(f"\n👤 Step 3: ایجاد کاربر...")
    try:
        create_user_response = requests.post(
            f"{BASE_URL}/admin/contractors/{contractor['id']}/create-user",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )
        
        if create_user_response.status_code == 201:
            user_data = create_user_response.json()
            print("✅ کاربر با موفقیت ایجاد شد!")
            print(f"  Username: {user_data['username']}")
            print(f"  Password: {user_data['password']}")
            # Update username and password for test
            username = user_data['username']
            password = user_data['password']
        elif create_user_response.status_code == 400:
            error_data = create_user_response.json()
            if error_data.get("error") == "user_exists":
                print("⚠️  کاربر از قبل وجود دارد")
                existing_username = error_data.get('username')
                print(f"  Username موجود: {existing_username}")
                # Use existing username and recalculate password
                username = existing_username
                # Password should be based on contractor's actual detail_code
                detail_code_actual = contractor['detail_code']
                password = f"{detail_code_actual}@{contractor['supplier_code']}"
                print(f"  Password محاسبه شده: {password}")
            else:
                print(f"❌ خطا: {error_data.get('message', 'Unknown error')}")
                return
        else:
            print(f"❌ خطا در ایجاد کاربر: {create_user_response.status_code}")
            print(f"   Response: {create_user_response.text}")
            return
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return
    
    # Step 4: Test login
    print(f"\n🔐 Step 4: تست Login با username و password تولید شده...")
    try:
        test_login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        
        if test_login_response.status_code == 200:
            print("✅ Login موفق بود!")
            login_data = test_login_response.json()
            print(f"  Access Token: {login_data['access_token'][:20]}...")
            if login_data.get("contractor"):
                print(f"  Contractor: {login_data['contractor']['name']}")
        else:
            print(f"❌ Login ناموفق: {test_login_response.status_code}")
            error_data = test_login_response.json()
            print(f"   Error: {error_data.get('error', 'Unknown')}")
            print(f"   Message: {error_data.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ تست کامل شد!")
    print("=" * 60)
    print(f"\n📋 اطلاعات ورود:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")

if __name__ == "__main__":
    main()

