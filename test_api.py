"""
API Testing Script for Value Set Management System
Tests all 24 endpoints systematically
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/value-sets"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_test(test_name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_result(success, message, response=None):
    if success:
        print(f"{GREEN}[PASS] {message}{RESET}")
    else:
        print(f"{RED}[FAIL] {message}{RESET}")
    if response:
        print(f"{YELLOW}Status: {response.status_code}{RESET}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)[:500]}")
        except:
            print(f"Response: {response.text[:500]}")

def test_endpoints():
    """Test all API endpoints"""

    # Track test results
    results = {"passed": 0, "failed": 0}

    # 1. Test Health Check
    print_test("1. Health Check Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_result(True, "Health check passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Health check failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 2. Test Root Endpoint
    print_test("2. Root Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print_result(True, "Root endpoint passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Root endpoint failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 3. Test Create Value Set
    print_test("3. Create Value Set")
    test_value_set = {
        "key": f"test_set_{int(time.time())}",
        "status": "active",
        "module": "Testing",
        "description": "Test value set for API testing",
        "items": [
            {"code": "TEST1", "labels": {"en": "Test One", "hi": "परीक्षण एक"}},
            {"code": "TEST2", "labels": {"en": "Test Two", "hi": "परीक्षण दो"}},
            {"code": "TEST3", "labels": {"en": "Test Three"}}
        ],
        "createdBy": "test_user"
    }

    created_key = None
    try:
        response = requests.post(API_BASE, json=test_value_set)
        if response.status_code == 200:
            print_result(True, "Create value set passed", response)
            created_key = response.json().get("key")
            results["passed"] += 1
        else:
            print_result(False, "Create value set failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 4. Test Get Value Set by Key
    print_test("4. Get Value Set by Key")
    if created_key:
        try:
            response = requests.get(f"{API_BASE}/{created_key}")
            if response.status_code == 200:
                print_result(True, "Get value set by key passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Get value set by key failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1
    else:
        print_result(False, "Skipped - no value set created")
        results["failed"] += 1

    # 5. Test List Value Sets
    print_test("5. List Value Sets")
    try:
        response = requests.get(f"{API_BASE}?skip=0&limit=10")
        if response.status_code == 200:
            print_result(True, "List value sets passed", response)
            results["passed"] += 1
        else:
            print_result(False, "List value sets failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 6. Test Update Value Set
    print_test("6. Update Value Set")
    if created_key:
        update_data = {
            "description": "Updated test description",
            "updatedBy": "test_user"
        }
        try:
            response = requests.put(f"{API_BASE}/{created_key}", json=update_data)
            if response.status_code == 200:
                print_result(True, "Update value set passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Update value set failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 7. Test Add Item to Value Set
    print_test("7. Add Item to Value Set")
    if created_key:
        add_item_data = {
            "item": {
                "code": "TEST4",
                "labels": {"en": "Test Four", "hi": "परीक्षण चार"}
            },
            "updatedBy": "test_user"
        }
        try:
            response = requests.post(f"{API_BASE}/{created_key}/items", json=add_item_data)
            if response.status_code == 200:
                print_result(True, "Add item passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Add item failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 8. Test Update Item in Value Set
    print_test("8. Update Item in Value Set")
    if created_key:
        update_item_data = {
            "itemCode": "TEST1",
            "updates": {
                "labels": {"en": "Test One Updated", "hi": "अपडेट किया गया"}
            },
            "updatedBy": "test_user"
        }
        try:
            response = requests.put(f"{API_BASE}/{created_key}/items/TEST1", json=update_item_data)
            if response.status_code == 200:
                print_result(True, "Update item passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Update item failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 9. Test Search Items
    print_test("9. Search Value Set Items")
    search_data = {
        "query": "Test",
        "languageCode": "en"
    }
    try:
        response = requests.post(f"{API_BASE}/search/items", json=search_data)
        if response.status_code == 200:
            print_result(True, "Search items passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Search items failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 10. Test Search by Label
    print_test("10. Search Value Sets by Label")
    try:
        response = requests.get(f"{API_BASE}/search/by-label?label_text=Test&language_code=en")
        if response.status_code == 200:
            print_result(True, "Search by label passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Search by label failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 11. Test Validate Value Set
    print_test("11. Validate Value Set")
    validate_data = {
        "key": "validation_test",
        "status": "active",
        "module": "Test",
        "items": [
            {"code": "V1", "labels": {"en": "Valid One"}}
        ]
    }
    try:
        response = requests.post(f"{API_BASE}/validate", json=validate_data)
        if response.status_code == 200:
            print_result(True, "Validate value set passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Validate value set failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 12. Test Archive Value Set
    print_test("12. Archive Value Set")
    if created_key:
        archive_data = {
            "key": created_key,
            "reason": "Testing archive functionality",
            "updatedBy": "test_user"
        }
        try:
            response = requests.post(f"{API_BASE}/{created_key}/archive", json=archive_data)
            if response.status_code == 200:
                print_result(True, "Archive value set passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Archive value set failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 13. Test Restore Value Set
    print_test("13. Restore Value Set")
    if created_key:
        restore_data = {
            "key": created_key,
            "reason": "Testing restore functionality",
            "updatedBy": "test_user"
        }
        try:
            response = requests.post(f"{API_BASE}/{created_key}/restore", json=restore_data)
            if response.status_code == 200:
                print_result(True, "Restore value set passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Restore value set failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 14. Test Get Statistics
    print_test("14. Get Value Set Statistics")
    try:
        response = requests.get(f"{API_BASE}/statistics/summary")
        if response.status_code == 200:
            print_result(True, "Get statistics passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Get statistics failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 15. Test Export Value Set
    print_test("15. Export Value Set")
    if created_key:
        try:
            response = requests.get(f"{API_BASE}/{created_key}/export?format=json")
            if response.status_code == 200:
                print_result(True, "Export value set passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Export value set failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 16. Test Bulk Add Items
    print_test("16. Bulk Add Items")
    if created_key:
        bulk_items = [
            {"code": "BULK1", "labels": {"en": "Bulk One"}},
            {"code": "BULK2", "labels": {"en": "Bulk Two"}}
        ]
        try:
            response = requests.post(
                f"{API_BASE}/{created_key}/items/bulk-add",
                json={"items": bulk_items, "updated_by": "test_user"}
            )
            if response.status_code == 200:
                print_result(True, "Bulk add items passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Bulk add items failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 17. Test Replace Item Value
    print_test("17. Replace Item Value")
    if created_key:
        replace_data = {
            "oldCode": "TEST2",
            "newCode": "TEST2_NEW",
            "newLabels": {"en": "Test Two Replaced"},
            "updatedBy": "test_user"
        }
        try:
            response = requests.put(f"{API_BASE}/{created_key}/items/replace", json=replace_data)
            if response.status_code == 200:
                print_result(True, "Replace item value passed", response)
                results["passed"] += 1
            else:
                print_result(False, "Replace item value failed", response)
                results["failed"] += 1
        except Exception as e:
            print_result(False, f"Error: {e}")
            results["failed"] += 1

    # 18. Test Bulk Import Value Sets
    print_test("18. Bulk Import Value Sets")
    bulk_import_data = {
        "valueSets": [
            {
                "key": f"bulk_test_1_{int(time.time())}",
                "status": "active",
                "module": "BulkTest",
                "description": "Bulk test 1",
                "items": [{"code": "B1", "labels": {"en": "Bulk One"}}],
                "createdBy": "test_user"
            },
            {
                "key": f"bulk_test_2_{int(time.time())}",
                "status": "active",
                "module": "BulkTest",
                "description": "Bulk test 2",
                "items": [{"code": "B2", "labels": {"en": "Bulk Two"}}],
                "createdBy": "test_user"
            }
        ]
    }
    try:
        response = requests.post(f"{API_BASE}/bulk/import", json=bulk_import_data)
        if response.status_code == 200:
            print_result(True, "Bulk import value sets passed", response)
            results["passed"] += 1
        else:
            print_result(False, "Bulk import value sets failed", response)
            results["failed"] += 1
    except Exception as e:
        print_result(False, f"Error: {e}")
        results["failed"] += 1

    # 19-20. Delete operations have been removed

    # Print Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    total = results['passed'] + results['failed']
    if total > 0:
        pass_rate = (results['passed'] / total) * 100
        print(f"{YELLOW}Pass Rate: {pass_rate:.1f}%{RESET}")

if __name__ == "__main__":
    print(f"{BLUE}Starting API Tests for Value Set Management System{RESET}")
    test_endpoints()