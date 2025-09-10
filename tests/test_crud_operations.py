import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")

def print_success(message: str):
    print(f"{Colors.GREEN}[OK] {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR] {message}{Colors.ENDC}")

def print_info(message: str):
    print(f"{Colors.YELLOW}[INFO] {message}{Colors.ENDC}")

async def login_as_admin():
    """Login as admin and return token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/auth/login",
            data={"username": "admin", "password": "pass@123"}
        )
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Login failed: {response.text}")

async def test_create_operation(token: str):
    """Test CREATE operation"""
    print_test_header("CREATE OPERATION TEST")
    
    test_data = {
        "key": "testCrudStatus",
        "status": "active",
        "description": "Test CRUD status values",
        "items": [
            {"code": "NEW", "labels": {"en": "New", "hi": "Naya"}},
            {"code": "IN_PROGRESS", "labels": {"en": "In Progress", "hi": "Chalu"}},
            {"code": "COMPLETED", "labels": {"en": "Completed", "hi": "Purn"}}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Clean up first if exists
        await client.delete(f"{API_URL}/enums/testCrudStatus", headers=headers)
        
        response = await client.post(
            f"{API_URL}/enums",
            headers=headers,
            json=test_data
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"ValueSet created successfully")
            print_info(f"  Key: {data['key']}")
            print_info(f"  Status: {data['status']}")
            print_info(f"  Items count: {len(data['items'])}")
            print_info(f"  Created by: {data.get('created_by', 'N/A')}")
            return True
        else:
            print_error(f"Create failed: {response.status_code} - {response.text}")
            return False

async def test_read_operations(token: str):
    """Test READ operations"""
    print_test_header("READ OPERATIONS TEST")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: List all ValueSets
        print("1. Testing LIST operation...")
        response = await client.get(f"{API_URL}/enums", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"List operation successful - {len(data)} ValueSets found")
            
            # Find our test ValueSet
            test_found = any(item["key"] == "testCrudStatus" for item in data)
            if test_found:
                print_info("  Test ValueSet found in list")
            else:
                print_error("  Test ValueSet not found in list")
        else:
            print_error(f"List operation failed: {response.status_code}")
            return False
        
        # Test 2: Get specific ValueSet
        print("\n2. Testing GET BY KEY operation...")
        response = await client.get(f"{API_URL}/enums/testCrudStatus", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get by key successful")
            print_info(f"  Key: {data['key']}")
            print_info(f"  Status: {data['status']}")
            print_info(f"  Items count: {len(data['items'])}")
            
            # Verify items
            for item in data['items']:
                print_info(f"    - {item['code']}: {item['label']}")
        else:
            print_error(f"Get by key failed: {response.status_code}")
            return False
        
        # Test 3: Bootstrap operation
        print("\n3. Testing BOOTSTRAP operation...")
        response = await client.get(f"{API_URL}/enums/bootstrap", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Bootstrap operation successful")
            print_info(f"  Total ValueSets in bootstrap: {len(data['data'])}")
            
            if "testCrudStatus" in data['data']:
                test_items = data['data']['testCrudStatus']
                print_info(f"  Test ValueSet in bootstrap with {len(test_items)} items")
            else:
                print_error("  Test ValueSet not found in bootstrap")
        else:
            print_error(f"Bootstrap failed: {response.status_code}")
            return False
        
        # Test 4: Get with different language
        print("\n4. Testing GET WITH LANGUAGE parameter...")
        response = await client.get(f"{API_URL}/enums/testCrudStatus?lang=hi", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Get with Hindi language successful")
            for item in data['items']:
                print_info(f"    - {item['code']}: {item['label']}")
        else:
            print_error(f"Get with language failed: {response.status_code}")
        
        return True

async def test_update_operation(token: str):
    """Test UPDATE operation"""
    print_test_header("UPDATE OPERATION TEST")
    
    update_data = {
        "description": "Updated CRUD test status values",
        "items": [
            {"code": "NEW", "labels": {"en": "New", "hi": "Naya"}},
            {"code": "IN_PROGRESS", "labels": {"en": "In Progress", "hi": "Chalu"}},
            {"code": "COMPLETED", "labels": {"en": "Completed", "hi": "Purn"}},
            {"code": "CANCELLED", "labels": {"en": "Cancelled", "hi": "Radd"}},
            {"code": "ON_HOLD", "labels": {"en": "On Hold", "hi": "Rok"}}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.put(
            f"{API_URL}/enums/testCrudStatus",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Update operation successful")
            print_info(f"  Updated description: {data['description']}")
            print_info(f"  New items count: {len(data['items'])}")
            print_info(f"  Items:")
            for item in data['items']:
                print_info(f"    - {item['code']}: {item['labels']['en']}")
            return True
        else:
            print_error(f"Update failed: {response.status_code} - {response.text}")
            return False

async def test_partial_update(token: str):
    """Test partial update (only some fields)"""
    print_test_header("PARTIAL UPDATE TEST")
    
    partial_data = {
        "status": "inactive"
    }
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.put(
            f"{API_URL}/enums/testCrudStatus",
            headers=headers,
            json=partial_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Partial update successful")
            print_info(f"  Status changed to: {data['status']}")
            print_info(f"  Description preserved: {data['description']}")
            print_info(f"  Items preserved: {len(data['items'])} items")
            return True
        else:
            print_error(f"Partial update failed: {response.status_code}")
            return False

async def test_delete_operation(token: str):
    """Test DELETE (Archive) operation"""
    print_test_header("DELETE (ARCHIVE) OPERATION TEST")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # First verify it exists
        response = await client.get(f"{API_URL}/enums/testCrudStatus", headers=headers)
        if response.status_code != 200:
            print_error("ValueSet not found before delete test")
            return False
        
        # Perform archive
        response = await client.delete(f"{API_URL}/enums/testCrudStatus", headers=headers)
        
        if response.status_code == 204:
            print_success(f"Archive operation successful (204 No Content)")
            
            # Verify it's archived (should still exist but status=archived)
            response = await client.get(f"{API_URL}/enums/testCrudStatus", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'archived':
                    print_success(f"ValueSet properly archived (status: {data['status']})")
                else:
                    print_error(f"ValueSet not properly archived (status: {data['status']})")
            else:
                print_info("ValueSet not accessible after archive (expected behavior)")
            
            return True
        else:
            print_error(f"Archive failed: {response.status_code}")
            return False

async def test_error_scenarios(token: str):
    """Test error scenarios"""
    print_test_header("ERROR SCENARIOS TEST")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Get non-existent ValueSet
        print("1. Testing GET non-existent ValueSet...")
        response = await client.get(f"{API_URL}/enums/nonExistentKey", headers=headers)
        
        if response.status_code == 404:
            print_success("Correctly returned 404 for non-existent ValueSet")
        else:
            print_error(f"Expected 404, got {response.status_code}")
        
        # Test 2: Create duplicate key
        print("\n2. Testing CREATE with duplicate key...")
        duplicate_data = {
            "key": "errorSeverity",  # This key should already exist
            "status": "active",
            "description": "Duplicate test",
            "items": [{"code": "TEST", "labels": {"en": "Test"}}]
        }
        
        response = await client.post(f"{API_URL}/enums", headers=headers, json=duplicate_data)
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "already exists" in error_detail:
                print_success("Correctly prevented duplicate key creation")
            else:
                print_error(f"Wrong error message: {error_detail}")
        else:
            print_error(f"Expected 400, got {response.status_code}")
        
        # Test 3: Update non-existent ValueSet
        print("\n3. Testing UPDATE non-existent ValueSet...")
        response = await client.put(
            f"{API_URL}/enums/nonExistentKey",
            headers=headers,
            json={"description": "test"}
        )
        
        if response.status_code == 404:
            print_success("Correctly returned 404 for update of non-existent ValueSet")
        else:
            print_error(f"Expected 404, got {response.status_code}")
        
        # Test 4: Delete non-existent ValueSet
        print("\n4. Testing DELETE non-existent ValueSet...")
        response = await client.delete(f"{API_URL}/enums/nonExistentKey", headers=headers)
        
        if response.status_code == 404:
            print_success("Correctly returned 404 for delete of non-existent ValueSet")
        else:
            print_error(f"Expected 404, got {response.status_code}")

async def main():
    """Run comprehensive CRUD tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*70)
    print("         COMPREHENSIVE CRUD OPERATIONS TEST")
    print("="*70)
    print(f"{Colors.ENDC}")
    
    try:
        # Login
        print_info("Logging in as admin...")
        token = await login_as_admin()
        print_success("Login successful")
        
        # Run all CRUD tests
        tests_passed = 0
        total_tests = 6
        
        if await test_create_operation(token):
            tests_passed += 1
        
        if await test_read_operations(token):
            tests_passed += 1
        
        if await test_update_operation(token):
            tests_passed += 1
        
        if await test_partial_update(token):
            tests_passed += 1
        
        if await test_delete_operation(token):
            tests_passed += 1
        
        # Error scenarios don't count toward main CRUD tests
        await test_error_scenarios(token)
        
        # Summary
        print_test_header("TEST SUMMARY")
        if tests_passed == total_tests:
            print_success(f"ALL CRUD TESTS PASSED! ({tests_passed}/{total_tests})")
        else:
            print_error(f"SOME TESTS FAILED! ({tests_passed}/{total_tests} passed)")
        
        print_info("\nTested operations:")
        print_info("  - CREATE - New ValueSet creation")
        print_info("  - READ - List, Get by key, Bootstrap, Language support")
        print_info("  - UPDATE - Full and partial updates")
        print_info("  - DELETE - Archive operation")
        print_info("  - ERROR HANDLING - 404s, duplicates, validation")
        
    except Exception as e:
        print_error(f"Test setup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())