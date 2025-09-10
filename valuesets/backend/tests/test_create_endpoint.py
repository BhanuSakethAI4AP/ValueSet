import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api/v1"

async def test_create_valueset():
    """Test the fixed create endpoint"""
    
    # First, login as admin
    async with httpx.AsyncClient() as client:
        # Login
        print("1. Logging in as admin...")
        response = await client.post(
            f"{API_URL}/auth/login",
            data={"username": "admin", "password": "pass@123"}
        )
        
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   Login successful!")
        
        # Create a new ValueSet
        print("\n2. Creating new ValueSet...")
        test_valueset = {
            "key": "testStatus",
            "status": "active",
            "description": "Test status values",
            "items": [
                {"code": "PENDING", "labels": {"en": "Pending", "hi": "लंबित"}},
                {"code": "APPROVED", "labels": {"en": "Approved", "hi": "मंजूर"}},
                {"code": "REJECTED", "labels": {"en": "Rejected", "hi": "अस्वीकृत"}}
            ],
            "created_by": "admin"  # This will be overridden by the API
        }
        
        response = await client.post(
            f"{API_URL}/enums",
            headers=headers,
            json=test_valueset
        )
        
        if response.status_code == 201:
            print(f"   SUCCESS! ValueSet created successfully")
            created_data = response.json()
            print(f"   Key: {created_data['key']}")
            print(f"   Created by: {created_data.get('created_by', 'N/A')}")
            print(f"   Items: {len(created_data['items'])} items")
            
            # Verify by getting the ValueSet
            print("\n3. Verifying created ValueSet...")
            response = await client.get(
                f"{API_URL}/enums/testStatus",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ValueSet retrieved successfully!")
                print(f"   Status: {data['status']}")
                print(f"   Items:")
                for item in data['items']:
                    print(f"     - {item['code']}: {item['label']}")
            
            # Update the ValueSet
            print("\n4. Updating ValueSet...")
            update_data = {
                "description": "Updated test status values",
                "items": [
                    {"code": "PENDING", "labels": {"en": "Pending", "hi": "लंबित"}},
                    {"code": "APPROVED", "labels": {"en": "Approved", "hi": "मंजूर"}},
                    {"code": "REJECTED", "labels": {"en": "Rejected", "hi": "अस्वीकृत"}},
                    {"code": "CANCELLED", "labels": {"en": "Cancelled", "hi": "रद्द"}}
                ]
            }
            
            response = await client.put(
                f"{API_URL}/enums/testStatus",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                print(f"   ValueSet updated successfully!")
                print(f"   New item count: {len(response.json()['items'])}")
            else:
                print(f"   Update failed: {response.status_code}")
            
            # Archive the ValueSet
            print("\n5. Archiving ValueSet...")
            response = await client.delete(
                f"{API_URL}/enums/testStatus",
                headers=headers
            )
            
            if response.status_code == 204:
                print(f"   ValueSet archived successfully!")
            else:
                print(f"   Archive failed: {response.status_code}")
                
        elif response.status_code == 400:
            error = response.json()
            if "already exists" in error.get("detail", ""):
                print(f"   ValueSet already exists. Cleaning up...")
                # Try to delete it first
                await client.delete(f"{API_URL}/enums/testStatus", headers=headers)
                print("   Please run the test again.")
            else:
                print(f"   Create failed (400): {error}")
        else:
            print(f"   Create failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(test_create_valueset())