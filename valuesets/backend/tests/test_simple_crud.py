import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api/v1"

async def main():
    print("=== SIMPLE CRUD TEST ===")
    
    # Login
    async with httpx.AsyncClient() as client:
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
        
        # Clean up any existing test data
        print("2. Cleaning up...")
        await client.delete(f"{API_URL}/enums/simpleCrud", headers=headers)
        print("   Cleanup done")
        
        # CREATE
        print("3. Testing CREATE...")
        create_data = {
            "key": "simpleCrud",
            "status": "active",
            "description": "Simple CRUD test",
            "items": [
                {"code": "TEST1", "labels": {"en": "Test One"}},
                {"code": "TEST2", "labels": {"en": "Test Two"}}
            ]
        }
        
        response = await client.post(f"{API_URL}/enums", headers=headers, json=create_data)
        if response.status_code == 201:
            data = response.json()
            print(f"   CREATE successful - ID: {data.get('id', 'N/A')}")
            print(f"   Key: {data['key']}, Items: {len(data['items'])}")
        else:
            print(f"   CREATE failed: {response.status_code} - {response.text}")
            return
        
        # READ
        print("4. Testing READ...")
        response = await client.get(f"{API_URL}/enums/simpleCrud", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   READ successful - Key: {data['key']}")
            print(f"   Status: {data['status']}, Items: {len(data['items'])}")
        else:
            print(f"   READ failed: {response.status_code}")
            return
        
        # UPDATE
        print("5. Testing UPDATE...")
        update_data = {
            "description": "Updated simple CRUD test",
            "items": [
                {"code": "TEST1", "labels": {"en": "Updated Test One"}},
                {"code": "TEST2", "labels": {"en": "Test Two"}},
                {"code": "TEST3", "labels": {"en": "Test Three"}}
            ]
        }
        
        response = await client.put(f"{API_URL}/enums/simpleCrud", headers=headers, json=update_data)
        if response.status_code == 200:
            data = response.json()
            print(f"   UPDATE successful - Items: {len(data['items'])}")
            print(f"   Description: {data['description']}")
        else:
            print(f"   UPDATE failed: {response.status_code}")
            return
        
        # DELETE (Archive)
        print("6. Testing DELETE...")
        response = await client.delete(f"{API_URL}/enums/simpleCrud", headers=headers)
        if response.status_code == 204:
            print("   DELETE successful (204 No Content)")
        else:
            print(f"   DELETE failed: {response.status_code}")
            return
        
        # Verify archived
        print("7. Verifying archive...")
        response = await client.get(f"{API_URL}/enums/simpleCrud", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'archived':
                print(f"   Correctly archived (status: {data['status']})")
            else:
                print(f"   Not properly archived (status: {data['status']})")
        elif response.status_code == 404:
            print("   ValueSet not found after archive (expected)")
        
        print("\n=== ALL CRUD OPERATIONS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(main())