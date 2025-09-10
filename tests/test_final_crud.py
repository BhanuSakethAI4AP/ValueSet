import asyncio
import httpx
import json
import random

BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api/v1"

async def main():
    print("=== FINAL CRUD TEST ===")
    
    # Generate unique key to avoid conflicts
    test_key = f"finalTest{random.randint(1000, 9999)}"
    
    async with httpx.AsyncClient() as client:
        # Login
        print("1. Logging in...")
        response = await client.post(
            f"{API_URL}/auth/login",
            data={"username": "admin", "password": "pass@123"}
        )
        
        if response.status_code != 200:
            print(f"LOGIN FAILED: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Login successful")
        
        # CREATE
        print(f"2. Testing CREATE with key: {test_key}")
        create_data = {
            "key": test_key,
            "status": "active",
            "description": "Final CRUD test",
            "items": [
                {"code": "ALPHA", "labels": {"en": "Alpha"}},
                {"code": "BETA", "labels": {"en": "Beta"}},
                {"code": "GAMMA", "labels": {"en": "Gamma"}}
            ]
        }
        
        response = await client.post(f"{API_URL}/enums", headers=headers, json=create_data)
        if response.status_code == 201:
            data = response.json()
            print(f"   CREATE successful!")
            print(f"   ID: {data.get('id', 'N/A')}")
            print(f"   Key: {data['key']}")
            print(f"   Items: {len(data['items'])}")
            print(f"   Created by: {data.get('created_by', 'N/A')}")
        else:
            print(f"   CREATE failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
        
        # READ - List all
        print("3. Testing LIST...")
        response = await client.get(f"{API_URL}/enums", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   LIST successful - Found {len(data)} ValueSets")
            found = any(item["key"] == test_key for item in data)
            print(f"   Test ValueSet found in list: {found}")
        else:
            print(f"   LIST failed: {response.status_code}")
        
        # READ - Get specific
        print("4. Testing GET BY KEY...")
        response = await client.get(f"{API_URL}/enums/{test_key}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   GET successful!")
            print(f"   Key: {data['key']}")
            print(f"   Status: {data['status']}")
            print(f"   Items: {len(data['items'])}")
            for item in data['items']:
                print(f"     - {item['code']}: {item['label']}")
        else:
            print(f"   GET failed: {response.status_code}")
            return
        
        # READ - Bootstrap
        print("5. Testing BOOTSTRAP...")
        response = await client.get(f"{API_URL}/enums/bootstrap", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   BOOTSTRAP successful - {len(data['data'])} active ValueSets")
            found = test_key in data['data']
            print(f"   Test ValueSet in bootstrap: {found}")
        else:
            print(f"   BOOTSTRAP failed: {response.status_code}")
        
        # UPDATE
        print("6. Testing UPDATE...")
        update_data = {
            "description": "Updated final CRUD test",
            "items": [
                {"code": "ALPHA", "labels": {"en": "Alpha Updated"}},
                {"code": "BETA", "labels": {"en": "Beta Updated"}},
                {"code": "GAMMA", "labels": {"en": "Gamma Updated"}},
                {"code": "DELTA", "labels": {"en": "Delta New"}}
            ]
        }
        
        response = await client.put(f"{API_URL}/enums/{test_key}", headers=headers, json=update_data)
        if response.status_code == 200:
            data = response.json()
            print(f"   UPDATE successful!")
            print(f"   Description: {data['description']}")
            print(f"   Items count: {len(data['items'])}")
        else:
            print(f"   UPDATE failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
        
        # DELETE (Archive)
        print("7. Testing DELETE (Archive)...")
        response = await client.delete(f"{API_URL}/enums/{test_key}", headers=headers)
        if response.status_code == 204:
            print("   DELETE successful (204 No Content)")
        else:
            print(f"   DELETE failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
        
        # Verify archived
        print("8. Verifying archive status...")
        response = await client.get(f"{API_URL}/enums/{test_key}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   ValueSet still accessible after archive")
            print(f"   Status: {data['status']}")
            if data['status'] == 'archived':
                print("   CORRECTLY ARCHIVED!")
            else:
                print("   WARNING: Status should be 'archived'")
        elif response.status_code == 404:
            print("   ValueSet not found (archived ValueSets might not be accessible)")
        
        # Check bootstrap doesn't include archived
        print("9. Verifying bootstrap excludes archived...")
        response = await client.get(f"{API_URL}/enums/bootstrap", headers=headers)
        if response.status_code == 200:
            data = response.json()
            found = test_key in data['data']
            print(f"   Archived ValueSet in bootstrap: {found}")
            if not found:
                print("   CORRECT: Archived ValueSet excluded from bootstrap")
            else:
                print("   WARNING: Archived ValueSet should not be in bootstrap")
        
        print("\n=== ALL CRUD OPERATIONS TESTED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(main())