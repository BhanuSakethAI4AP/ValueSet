"""
Comprehensive Test Suite for Value Set Management System
Tests all CRUD operations, search functionality, and edge cases
File: tests/test.py
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import json

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from database import connect_to_mongodb, disconnect_from_mongodb, get_database
from services.value_set_service import ValueSetService
from repositories.value_set_repository import ValueSetRepository
from schemas.value_set_schemas_enhanced import (
    ValueSetCreateSchema, ValueSetUpdateSchema,
    ItemCreateSchema, ItemUpdateSchema, LabelSchema,
    AddItemRequestSchema, UpdateItemRequestSchema,
    ReplaceItemCodeSchema, BulkValueSetCreateSchema,
    ArchiveRestoreRequestSchema, ListValueSetsQuerySchema,
    SearchItemsQuerySchema, StatusEnum
)


class TestResults:
    """Track test results and statistics"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.test_data = {}

    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed += 1
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   Details: {details}")

    def add_fail(self, test_name: str, error: str, details: str = ""):
        self.total += 1
        self.failed += 1
        self.errors.append({"test": test_name, "error": error, "details": details})
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
        if details:
            print(f"   Details: {details}")

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/self.total*100) if self.total > 0 else 0:.2f}%")

        if self.errors:
            print("\n" + "="*80)
            print("FAILED TESTS DETAILS")
            print("="*80)
            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. {error['test']}")
                print(f"   Error: {error['error']}")
                if error['details']:
                    print(f"   Details: {error['details']}")

        print("\n" + "="*80)


class ValueSetTester:
    """Comprehensive test suite for Value Set Management System"""

    def __init__(self):
        self.results = TestResults()
        self.service = None
        self.repository = None
        self.db = None
        self.created_keys = []

    async def setup(self):
        """Initialize database connection and services"""
        print("="*80)
        print("SETTING UP TEST ENVIRONMENT")
        print("="*80)
        try:
            await connect_to_mongodb()
            self.db = get_database()
            self.repository = ValueSetRepository(self.db)
            self.service = ValueSetService(self.repository)
            print("✅ Database connected successfully")
            print(f"   Database: {os.getenv('DB_NAME')}")
            return True
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return False

    async def cleanup(self):
        """Clean up test data and disconnect"""
        print("\n" + "="*80)
        print("CLEANING UP TEST DATA")
        print("="*80)

        deleted_count = 0
        for key in self.created_keys:
            try:
                collection = self.db.value_sets
                result = await collection.delete_one({"key": key})
                if result.deleted_count > 0:
                    deleted_count += 1
                    print(f"   Deleted: {key}")
            except Exception as e:
                print(f"   Failed to delete {key}: {e}")

        print(f"✅ Cleaned up {deleted_count}/{len(self.created_keys)} test records")

        await disconnect_from_mongodb()
        print("✅ Database disconnected")

    # ==================== CREATE TESTS ====================

    async def test_create_basic_value_set(self):
        """Test basic value set creation with minimal data"""
        test_name = "Create Basic Value Set"
        try:
            key = f"TEST_BASIC_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [
                ItemCreateSchema(
                    code="ITEM001",
                    labels=LabelSchema(en="Item One", hi="आइटम एक")
                ),
                ItemCreateSchema(
                    code="ITEM002",
                    labels=LabelSchema(en="Item Two", hi="आइटम दो")
                )
            ]

            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                description="Basic test value set",
                items=items,
                createdBy="test_user"
            )

            result = await self.service.create_value_set(create_data)

            if result.key == key and len(result.items) == 2:
                self.results.add_pass(
                    test_name,
                    f"Created value set '{key}' with {len(result.items)} items"
                )
                self.results.test_data['basic_value_set'] = result.model_dump()
            else:
                self.results.add_fail(test_name, "Result validation failed")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_create_value_set_with_max_items(self):
        """Test creating value set with maximum allowed items (500)"""
        test_name = "Create Value Set with Max Items (500)"
        try:
            key = f"TEST_MAX_ITEMS_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [
                ItemCreateSchema(
                    code=f"CODE_{i:04d}",
                    labels=LabelSchema(en=f"Item {i}", hi=f"आइटम {i}")
                )
                for i in range(1, 501)
            ]

            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                description="Value set with maximum items",
                items=items,
                createdBy="test_user"
            )

            result = await self.service.create_value_set(create_data)

            if len(result.items) == 500:
                self.results.add_pass(
                    test_name,
                    f"Successfully created value set with 500 items"
                )
            else:
                self.results.add_fail(test_name, f"Expected 500 items, got {len(result.items)}")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_create_duplicate_key(self):
        """Test that creating duplicate key fails"""
        test_name = "Create Duplicate Key (Should Fail)"
        try:
            key = f"TEST_DUPLICATE_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="TEST", labels=LabelSchema(en="Test"))]

            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            try:
                await self.service.create_value_set(create_data)
                self.results.add_fail(test_name, "Duplicate key was allowed (should have failed)")
            except ValueError as ve:
                if "already exists" in str(ve):
                    self.results.add_pass(test_name, "Correctly rejected duplicate key")
                else:
                    self.results.add_fail(test_name, f"Wrong error: {ve}")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_create_with_duplicate_item_codes(self):
        """Test that duplicate item codes within value set are rejected"""
        test_name = "Create with Duplicate Item Codes (Should Fail)"
        try:
            key = f"TEST_DUP_ITEMS_{datetime.utcnow().timestamp()}"

            items = [
                ItemCreateSchema(code="DUP", labels=LabelSchema(en="First")),
                ItemCreateSchema(code="DUP", labels=LabelSchema(en="Second"))
            ]

            try:
                create_data = ValueSetCreateSchema(
                    key=key,
                    status=StatusEnum.ACTIVE,
                    module="Testing",
                    items=items,
                    createdBy="test_user"
                )

                await self.service.create_value_set(create_data)
                self.results.add_fail(test_name, "Duplicate item codes were allowed")
            except Exception as ve:
                if "unique" in str(ve).lower() or "validation error" in str(ve).lower():
                    self.results.add_pass(test_name, "Correctly rejected duplicate item codes (Pydantic validation)")
                else:
                    self.results.add_fail(test_name, f"Wrong error: {ve}")

        except Exception as e:
            if "unique" in str(e).lower() or "validation error" in str(e).lower():
                self.results.add_pass(test_name, "Correctly rejected duplicate item codes (Pydantic validation)")
            else:
                self.results.add_fail(test_name, str(e))

    # ==================== READ TESTS ====================

    async def test_get_value_set_by_key(self):
        """Test retrieving value set by key"""
        test_name = "Get Value Set by Key"
        try:
            key = f"TEST_GET_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="GET001", labels=LabelSchema(en="Get Test"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            result = await self.service.get_value_set_by_key(key)

            if result and result.key == key:
                self.results.add_pass(test_name, f"Retrieved value set '{key}'")
            else:
                self.results.add_fail(test_name, "Failed to retrieve value set")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_get_nonexistent_value_set(self):
        """Test retrieving non-existent value set returns None"""
        test_name = "Get Non-existent Value Set"
        try:
            result = await self.service.get_value_set_by_key("NONEXISTENT_KEY_12345")

            if result is None:
                self.results.add_pass(test_name, "Correctly returned None for non-existent key")
            else:
                self.results.add_fail(test_name, "Should return None for non-existent key")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_list_value_sets(self):
        """Test listing value sets with pagination"""
        test_name = "List Value Sets with Pagination"
        try:
            keys = []
            for i in range(5):
                key = f"TEST_LIST_{i}_{datetime.utcnow().timestamp()}"
                keys.append(key)
                self.created_keys.append(key)

                items = [ItemCreateSchema(code=f"L{i}", labels=LabelSchema(en=f"List {i}"))]
                create_data = ValueSetCreateSchema(
                    key=key,
                    status=StatusEnum.ACTIVE,
                    module="ListTest",
                    items=items,
                    createdBy="test_user"
                )
                await self.service.create_value_set(create_data)

            query = ListValueSetsQuerySchema(
                status=StatusEnum.ACTIVE,
                module="ListTest",
                skip=0,
                limit=3
            )

            result = await self.service.list_value_sets(query)

            if result.total >= 5 and len(result.items) <= 3:
                self.results.add_pass(
                    test_name,
                    f"Listed {len(result.items)} of {result.total} value sets"
                )
            else:
                self.results.add_fail(test_name, f"Unexpected results: {len(result.items)} items")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== UPDATE TESTS ====================

    async def test_update_value_set_description(self):
        """Test updating value set description"""
        test_name = "Update Value Set Description"
        try:
            key = f"TEST_UPDATE_DESC_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="UPD", labels=LabelSchema(en="Update Test"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                description="Original description",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            update_data = ValueSetUpdateSchema(
                description="Updated description",
                updatedBy="test_updater"
            )

            result = await self.service.update_value_set(key, update_data)

            if result and result.description == "Updated description":
                self.results.add_pass(test_name, "Description updated successfully")
            else:
                self.results.add_fail(test_name, "Description not updated")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_update_value_set_status(self):
        """Test updating value set status"""
        test_name = "Update Value Set Status"
        try:
            key = f"TEST_UPDATE_STATUS_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="STS", labels=LabelSchema(en="Status Test"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            update_data = ValueSetUpdateSchema(
                status=StatusEnum.ARCHIVED,
                updatedBy="test_updater"
            )

            result = await self.service.update_value_set(key, update_data)

            if result and result.status == "archived":
                self.results.add_pass(test_name, "Status updated to archived")
            else:
                self.results.add_fail(test_name, f"Status not updated correctly: {result.status}")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== ITEM MANAGEMENT TESTS ====================

    async def test_add_item_to_value_set(self):
        """Test adding item to existing value set"""
        test_name = "Add Item to Value Set"
        try:
            key = f"TEST_ADD_ITEM_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="ORIG", labels=LabelSchema(en="Original"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            new_item = ItemCreateSchema(code="NEW", labels=LabelSchema(en="New Item", hi="नया"))
            add_request = AddItemRequestSchema(item=new_item, updatedBy="test_user")

            result = await self.service.add_item_to_value_set(key, add_request)

            if result and len(result.items) == 2:
                self.results.add_pass(test_name, f"Added item, now has {len(result.items)} items")
            else:
                self.results.add_fail(test_name, "Item not added correctly")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_add_duplicate_item_code(self):
        """Test that adding duplicate item code fails"""
        test_name = "Add Duplicate Item Code (Should Fail)"
        try:
            key = f"TEST_DUP_ADD_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="DUP", labels=LabelSchema(en="Original"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            dup_item = ItemCreateSchema(code="DUP", labels=LabelSchema(en="Duplicate"))
            add_request = AddItemRequestSchema(item=dup_item, updatedBy="test_user")

            try:
                await self.service.add_item_to_value_set(key, add_request)
                self.results.add_fail(test_name, "Duplicate item code was allowed")
            except ValueError as ve:
                if "already exists" in str(ve):
                    self.results.add_pass(test_name, "Correctly rejected duplicate item code")
                else:
                    self.results.add_fail(test_name, f"Wrong error: {ve}")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_update_item_labels(self):
        """Test updating item labels"""
        test_name = "Update Item Labels"
        try:
            key = f"TEST_UPDATE_ITEM_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="UPD", labels=LabelSchema(en="Original Label"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            from schemas.value_set_schemas_enhanced import LabelUpdateSchema
            updates = ItemUpdateSchema(
                labels=LabelUpdateSchema(en="Updated Label", hi="अपडेट लेबल")
            )
            update_request = UpdateItemRequestSchema(
                itemCode="UPD",
                updates=updates,
                updatedBy="test_user"
            )

            result = await self.service.update_item_in_value_set(key, update_request)

            if result:
                updated_item = next((item for item in result.items if item.code == "UPD"), None)
                if updated_item and updated_item.labels.en == "Updated Label":
                    self.results.add_pass(test_name, "Item labels updated successfully")
                else:
                    self.results.add_fail(test_name, "Labels not updated correctly")
            else:
                self.results.add_fail(test_name, "Update failed")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_replace_item_code(self):
        """Test replacing item code"""
        test_name = "Replace Item Code"
        try:
            key = f"TEST_REPLACE_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="OLD", labels=LabelSchema(en="Old Code"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            replace_request = ReplaceItemCodeSchema(
                oldCode="OLD",
                newCode="NEW",
                newLabels=LabelSchema(en="New Code", hi="नया कोड"),
                updatedBy="test_user"
            )

            result = await self.service.replace_value_in_item(key, replace_request)

            if result:
                has_new = any(item.code == "NEW" for item in result.items)
                has_old = any(item.code == "OLD" for item in result.items)

                if has_new and not has_old:
                    self.results.add_pass(test_name, "Item code replaced successfully")
                else:
                    self.results.add_fail(test_name, f"Replace incomplete: has_new={has_new}, has_old={has_old}")
            else:
                self.results.add_fail(test_name, "Replace failed")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== SEARCH TESTS ====================

    async def test_search_value_set_items(self):
        """Test searching for items across value sets"""
        test_name = "Search Value Set Items"
        try:
            key = f"TEST_SEARCH_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [
                ItemCreateSchema(code="APPLE", labels=LabelSchema(en="Apple Fruit", hi="सेब")),
                ItemCreateSchema(code="BANANA", labels=LabelSchema(en="Banana Fruit", hi="केला")),
                ItemCreateSchema(code="ORANGE", labels=LabelSchema(en="Orange Fruit", hi="संतरा"))
            ]

            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Fruits",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            search_params = SearchItemsQuerySchema(
                query="Fruit",
                languageCode="en"
            )

            results = await self.service.search_value_set_items(search_params)

            matching_result = next((r for r in results if r.valueSetKey == key), None)

            if matching_result and matching_result.totalMatches == 3:
                self.results.add_pass(test_name, f"Found {matching_result.totalMatches} matching items")
            else:
                self.results.add_fail(test_name, "Search results incorrect")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_search_by_label(self):
        """Test searching value sets by label text"""
        test_name = "Search by Label"
        try:
            key = f"TEST_LABEL_SEARCH_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [
                ItemCreateSchema(code="ADM", labels=LabelSchema(en="Administrator Role")),
                ItemCreateSchema(code="USR", labels=LabelSchema(en="User Role"))
            ]

            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Roles",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            results = await self.service.search_value_sets_by_label("Administrator", "en")

            found = any(vs.key == key for vs in results)

            if found:
                self.results.add_pass(test_name, "Found value set by label search")
            else:
                self.results.add_fail(test_name, "Value set not found in search results")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== ARCHIVE/RESTORE TESTS ====================

    async def test_archive_value_set(self):
        """Test archiving a value set"""
        test_name = "Archive Value Set"
        try:
            key = f"TEST_ARCHIVE_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="ARC", labels=LabelSchema(en="Archive Test"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            archive_request = ArchiveRestoreRequestSchema(
                key=key,
                reason="Testing archive functionality",
                updatedBy="test_user"
            )

            result = await self.service.archive_value_set(archive_request)

            if result.success and result.currentStatus == "archived":
                self.results.add_pass(test_name, "Value set archived successfully")
            else:
                self.results.add_fail(test_name, "Archive operation failed")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_restore_value_set(self):
        """Test restoring an archived value set"""
        test_name = "Restore Value Set"
        try:
            key = f"TEST_RESTORE_{datetime.utcnow().timestamp()}"
            self.created_keys.append(key)

            items = [ItemCreateSchema(code="RES", labels=LabelSchema(en="Restore Test"))]
            create_data = ValueSetCreateSchema(
                key=key,
                status=StatusEnum.ARCHIVED,
                module="Testing",
                items=items,
                createdBy="test_user"
            )

            await self.service.create_value_set(create_data)

            restore_request = ArchiveRestoreRequestSchema(
                key=key,
                reason="Testing restore functionality",
                updatedBy="test_user"
            )

            result = await self.service.restore_value_set(restore_request)

            if result.success and result.currentStatus == "active":
                self.results.add_pass(test_name, "Value set restored successfully")
            else:
                self.results.add_fail(test_name, "Restore operation failed")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== BULK OPERATIONS TESTS ====================

    async def test_bulk_import_value_sets(self):
        """Test bulk importing multiple value sets"""
        test_name = "Bulk Import Value Sets"
        try:
            value_sets = []
            keys = []

            for i in range(3):
                key = f"TEST_BULK_{i}_{datetime.utcnow().timestamp()}"
                keys.append(key)
                self.created_keys.append(key)

                items = [ItemCreateSchema(code=f"B{i}", labels=LabelSchema(en=f"Bulk Item {i}"))]

                vs = ValueSetCreateSchema(
                    key=key,
                    status=StatusEnum.ACTIVE,
                    module="BulkTest",
                    items=items,
                    createdBy="test_user"
                )
                value_sets.append(vs)

            bulk_data = BulkValueSetCreateSchema(valueSets=value_sets)
            result = await self.service.bulk_import_value_sets(bulk_data)

            if result.successful == 3 and result.failed == 0:
                self.results.add_pass(test_name, f"Imported {result.successful} value sets")
            else:
                self.results.add_fail(
                    test_name,
                    f"Expected 3 successful, got {result.successful} successful, {result.failed} failed"
                )

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== VALIDATION TESTS ====================

    async def test_validate_valid_value_set(self):
        """Test validation of a valid value set"""
        test_name = "Validate Valid Value Set"
        try:
            from schemas.value_set_schemas_enhanced import ValidateValueSetRequestSchema, ItemSchema

            items = [
                ItemSchema(code="VAL1", labels=LabelSchema(en="Valid 1")),
                ItemSchema(code="VAL2", labels=LabelSchema(en="Valid 2"))
            ]

            validation_request = ValidateValueSetRequestSchema(
                key="TEST_VALIDATION",
                status=StatusEnum.ACTIVE,
                module="Testing",
                items=items
            )

            result = await self.service.validate_value_set(validation_request)

            if result.isValid and len(result.errors) == 0:
                self.results.add_pass(test_name, "Valid value set passed validation")
            else:
                self.results.add_fail(test_name, f"Validation failed: {result.errors}")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    async def test_validate_invalid_value_set(self):
        """Test validation of an invalid value set (duplicate codes)"""
        test_name = "Validate Invalid Value Set (Should Fail)"
        try:
            from schemas.value_set_schemas_enhanced import ValidateValueSetRequestSchema, ItemSchema

            items = [
                ItemSchema(code="DUP", labels=LabelSchema(en="Duplicate 1")),
                ItemSchema(code="DUP", labels=LabelSchema(en="Duplicate 2"))
            ]

            try:
                validation_request = ValidateValueSetRequestSchema(
                    key="TEST_INVALID",
                    status=StatusEnum.ACTIVE,
                    module="Testing",
                    items=items
                )

                result = await self.service.validate_value_set(validation_request)

                if not result.isValid and len(result.errors) > 0:
                    self.results.add_pass(test_name, f"Correctly detected validation errors: {result.errors}")
                else:
                    self.results.add_fail(test_name, "Should have detected duplicate codes")
            except Exception as ve:
                if "unique" in str(ve).lower() or "validation error" in str(ve).lower():
                    self.results.add_pass(test_name, "Correctly rejected at schema level (Pydantic validation)")
                else:
                    self.results.add_fail(test_name, f"Wrong error: {ve}")

        except Exception as e:
            if "unique" in str(e).lower() or "validation error" in str(e).lower():
                self.results.add_pass(test_name, "Correctly rejected at schema level (Pydantic validation)")
            else:
                self.results.add_fail(test_name, str(e))

    # ==================== STATISTICS TESTS ====================

    async def test_get_statistics(self):
        """Test retrieving value set statistics"""
        test_name = "Get Value Set Statistics"
        try:
            stats = await self.service.get_value_set_statistics()

            if 'total_value_sets' in stats and 'by_status' in stats:
                self.results.add_pass(
                    test_name,
                    f"Retrieved stats: {stats['total_value_sets']} total value sets"
                )
                self.results.test_data['statistics'] = stats
            else:
                self.results.add_fail(test_name, "Statistics structure incorrect")

        except Exception as e:
            self.results.add_fail(test_name, str(e))

    # ==================== MAIN TEST RUNNER ====================

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE VALUE SET TESTS")
        print("="*80)
        print(f"Test Start Time: {datetime.utcnow().isoformat()}\n")

        test_methods = [
            # CREATE
            self.test_create_basic_value_set,
            self.test_create_value_set_with_max_items,
            self.test_create_duplicate_key,
            self.test_create_with_duplicate_item_codes,

            # READ
            self.test_get_value_set_by_key,
            self.test_get_nonexistent_value_set,
            self.test_list_value_sets,

            # UPDATE
            self.test_update_value_set_description,
            self.test_update_value_set_status,

            # ITEM MANAGEMENT
            self.test_add_item_to_value_set,
            self.test_add_duplicate_item_code,
            self.test_update_item_labels,
            self.test_replace_item_code,

            # SEARCH
            self.test_search_value_set_items,
            self.test_search_by_label,

            # ARCHIVE/RESTORE
            self.test_archive_value_set,
            self.test_restore_value_set,

            # BULK
            self.test_bulk_import_value_sets,

            # VALIDATION
            self.test_validate_valid_value_set,
            self.test_validate_invalid_value_set,

            # STATISTICS
            self.test_get_statistics,
        ]

        for i, test_method in enumerate(test_methods, 1):
            print(f"\n[{i}/{len(test_methods)}] Running: {test_method.__name__}")
            print("-" * 80)
            await test_method()
            await asyncio.sleep(0.1)

        print(f"\nTest End Time: {datetime.utcnow().isoformat()}")
        self.results.print_summary()

        return self.results


async def main():
    """Main test execution function"""
    tester = ValueSetTester()

    if not await tester.setup():
        print("Failed to setup test environment. Exiting.")
        return

    try:
        results = await tester.run_all_tests()

        print("\n" + "="*80)
        print("SAVING TEST RESULTS")
        print("="*80)

        results_file = os.path.join(
            os.path.dirname(__file__),
            f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'total': results.total,
                    'passed': results.passed,
                    'failed': results.failed,
                    'success_rate': f"{(results.passed/results.total*100) if results.total > 0 else 0:.2f}%"
                },
                'errors': results.errors,
                'test_data': results.test_data
            }, f, indent=2, default=str)

        print(f"✅ Results saved to: {results_file}")

    finally:
        await tester.cleanup()

    print("\n" + "="*80)
    print("TEST EXECUTION COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())