"""
Quick script to create admin user via API
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1"

# 1. Register as admin
register_data = {
    "employee_id": "ADMIN001",
    "email": "admin@company.com",
    "name": "Admin User",
    "password": "Admin123!@#"
}

try:
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("✓ Admin user created!")
        print(f"  Employee ID: ADMIN001")
        print(f"  Password: Admin123!@#")
    elif response.status_code == 400:
        error = response.json()
        if "already exists" in error.get("message", "").lower():
            print("✓ User already exists")
        else:
            print(f"Error: {error}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Failed to connect to backend: {e}")
    print("\nMake sure backend server is running:")
    print("  uvicorn app.main:app --reload")

# 2. Register IT Staff
it_data = {
    "employee_id": "IT001",
    "email": "it@company.com",
    "name": "IT Staff",
    "password": "IT123!@#"
}

try:
    response = requests.post(f"{API_URL}/auth/register", json=it_data)
    if response.status_code == 201:
        print("\n✓ IT Staff user created!")
        print(f"  Employee ID: IT001")
        print(f"  Password: IT123!@#")
    elif response.status_code == 400:
        error = response.json()
        if "already exists" in error.get("message", "").lower():
            print("\n✓ IT Staff user already exists")
        else:
            print(f"\nError: {error}")
except Exception as e:
    print(f"\nFailed to create IT user: {e}")

print("\n" + "="*60)
print("NOTE: Users are created with EMPLOYEE role by default.")
print("You need to manually update their role to ADMIN or IT_STAFF in the database.")
print("="*60)
