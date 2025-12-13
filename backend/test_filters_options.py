"""
Test script for filters/options endpoint
"""
import requests
import json
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

# First, login to get a token
# Try different contractors to find the one being tested
login_data = {
    "username": "70358",
    "password": "70358@2024"
}

print("Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n" + "="*50)
print("Test 1: Get filter options WITHOUT any filters")
print("="*50)
response = requests.get(f"{BASE_URL}/invoices/filters/options", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Fiscal years: {data.get('fiscal_years', [])}")
    print(f"Statuses: {data.get('statuses', [])}")
    print(f"Status stats: {json.dumps(data.get('status_stats', {}), indent=2, ensure_ascii=False)}")

print("\n" + "="*50)
print("Test 2: Get filter options WITH fiscal_year=1404")
print("="*50)
response = requests.get(f"{BASE_URL}/invoices/filters/options?fiscal_year=1404", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Fiscal years: {data.get('fiscal_years', [])}")
    print(f"Statuses: {data.get('statuses', [])}")
    print(f"Status stats: {json.dumps(data.get('status_stats', {}), indent=2, ensure_ascii=False)}")

print("\n" + "="*50)
print("Test 3: Get filter options WITH fiscal_year=1403")
print("="*50)
response = requests.get(f"{BASE_URL}/invoices/filters/options?fiscal_year=1403", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Fiscal years: {data.get('fiscal_years', [])}")
    print(f"Statuses: {data.get('statuses', [])}")
    print(f"Status stats: {json.dumps(data.get('status_stats', {}), indent=2, ensure_ascii=False)}")

print("\n" + "="*50)
print("Test 4: Get filter options WITH fiscal_year=1404 (the one being tested)")
print("="*50)
response = requests.get(f"{BASE_URL}/invoices/filters/options?fiscal_year=1404", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Fiscal years: {data.get('fiscal_years', [])}")
    print(f"Statuses: {data.get('statuses', [])}")
    print(f"Status stats: {json.dumps(data.get('status_stats', {}), indent=2, ensure_ascii=False)}")
    
    # Check if only one status is returned
    statuses = data.get('statuses', [])
    if len(statuses) == 1:
        print(f"\n⚠️ WARNING: Only one status returned: {statuses[0]}")
        print("This is the problem!")

