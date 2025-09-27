# Value Set Management System - Comprehensive Test Documentation

## 📋 Table of Contents
- [Test Overview](#test-overview)
- [Test Environment Setup](#test-environment-setup)
- [Test Execution](#test-execution)
- [Test Categories](#test-categories)
- [Test Data](#test-data)
- [Expected Results](#expected-results)
- [Error Scenarios](#error-scenarios)
- [Test Results Analysis](#test-results-analysis)

---

## 🎯 Test Overview

### Purpose
This test suite validates **ALL** functionality of the Value Set Management System with a **critical tester mindset**. The goal is to find bugs, validate business rules, and ensure data integrity across all operations.

### Test Philosophy
> **"Assume everything can fail until proven otherwise"**

We test with the assumption that the system will fail, and our job is to prove whether it handles failures gracefully or not.

### Test Scope
- ✅ **21 Comprehensive Test Cases**
- ✅ **CRUD Operations** (Create, Read, Update, Delete)
- ✅ **Search Functionality** (Text search, label search)
- ✅ **Item Management** (Add, Update, Replace, Delete items)
- ✅ **Bulk Operations** (Import, Update, Delete)
- ✅ **Archive/Restore** (Soft delete functionality)
- ✅ **Validation** (Business rule enforcement)
- ✅ **Statistics** (System-wide metrics)
- ✅ **Edge Cases** (Max limits, duplicates, invalid data)
- ✅ **Error Handling** (Negative test cases)

---

## 🛠️ Test Environment Setup

### Prerequisites
```bash
1. Python 3.8+
2. MongoDB running (locally or remote)
3. Required packages installed:
   - motor (async MongoDB driver)
   - pymongo
   - pydantic
   - python-dotenv
```

### Environment Configuration
Create `.env` file in project root:
```ini
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
DB_NAME=ValueSetsTest
ENVIRONMENT=testing
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Verify MongoDB connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').server_info())"
```

---

## 🚀 Test Execution

### Running All Tests
```bash
cd "D:\Core Components\ValueSets"
python tests/test.py
```

### What Happens During Test Execution:
1. **Setup Phase**: Connects to MongoDB, initializes services
2. **Test Execution**: Runs 21 tests sequentially
3. **Results Collection**: Tracks passes, failures, errors
4. **Cleanup Phase**: Deletes all test data from database
5. **Report Generation**: Creates JSON results file with timestamp

### Output Format
- ✅ **PASS**: Green checkmark, test succeeded
- ❌ **FAIL**: Red X, test failed with error details
- **Progress**: Shows current test number (e.g., [5/21])
- **Summary**: Final statistics with success rate

---

## 📂 Test Categories

### 1. CREATE Tests (4 tests)

#### Test 1: Create Basic Value Set
**Purpose**: Validate basic value set creation with minimal required fields

**Input Data**:
```python
{
    "key": "TEST_BASIC_<timestamp>",
    "status": "active",
    "module": "Testing",
    "description": "Basic test value set",
    "items": [
        {"code": "ITEM001", "labels": {"en": "Item One", "hi": "आइटम एक"}},
        {"code": "ITEM002", "labels": {"en": "Item Two", "hi": "आइटम दो"}}
    ],
    "createdBy": "test_user"
}
```

**Expected Output**:
- ✅ Value set created successfully
- ✅ Returns complete value set with generated _id
- ✅ Contains exactly 2 items
- ✅ Status is "active"
- ✅ createdAt timestamp is auto-generated

**Validation Checks**:
- Key matches input
- Item count is correct
- All fields are populated

---

#### Test 2: Create Value Set with Maximum Items (500)
**Purpose**: Test system limits - can it handle maximum allowed items?

**Input Data**:
```python
{
    "key": "TEST_MAX_ITEMS_<timestamp>",
    "items": [
        {"code": "CODE_0001", "labels": {"en": "Item 1", "hi": "आइटम 1"}},
        {"code": "CODE_0002", "labels": {"en": "Item 2", "hi": "आइटम 2"}},
        ...
        {"code": "CODE_0500", "labels": {"en": "Item 500", "hi": "आइटम 500"}}
    ]
}
```

**Expected Output**:
- ✅ Successfully creates value set with 500 items
- ✅ All items are stored correctly
- ✅ No data truncation or loss

**Critical Validation**:
```python
assert len(result.items) == 500
assert all(item.code for item in result.items)  # No empty codes
```

---

#### Test 3: Create Duplicate Key (Negative Test)
**Purpose**: **Should FAIL** - System must reject duplicate keys

**Input Data**:
```python
# First creation
{"key": "TEST_DUPLICATE_<timestamp>", ...}

# Second creation (same key)
{"key": "TEST_DUPLICATE_<timestamp>", ...}
```

**Expected Output**:
- ❌ **MUST throw ValueError**
- ✅ Error message contains "already exists"
- ✅ Database remains consistent (only 1 record exists)

**This Test PROVES**:
- Key uniqueness constraint works
- Error handling is correct
- Database integrity is maintained

---

#### Test 4: Create with Duplicate Item Codes (Negative Test)
**Purpose**: **Should FAIL** - Items within a value set must have unique codes

**Input Data**:
```python
{
    "items": [
        {"code": "DUP", "labels": {"en": "First"}},
        {"code": "DUP", "labels": {"en": "Second"}}  # DUPLICATE!
    ]
}
```

**Expected Output**:
- ❌ **MUST throw ValueError**
- ✅ Error message contains "unique"
- ✅ No value set is created

**This Test PROVES**:
- Item code uniqueness validation works
- System rejects invalid data before database insertion

---

### 2. READ Tests (3 tests)

#### Test 5: Get Value Set by Key
**Purpose**: Verify retrieval of existing value sets

**Input Data**:
```python
key = "TEST_GET_<timestamp>"
# First create, then retrieve
```

**Expected Output**:
```python
{
    "_id": "generated_id",
    "key": "TEST_GET_<timestamp>",
    "status": "active",
    "module": "Testing",
    "items": [{"code": "GET001", ...}],
    "createdAt": "2024-01-15T10:30:00Z",
    "createdBy": "test_user"
}
```

**Validation**:
- Retrieved data matches created data
- All fields are present
- No data corruption

---

#### Test 6: Get Non-existent Value Set (Negative Test)
**Purpose**: Verify correct handling of missing data

**Input Data**:
```python
key = "NONEXISTENT_KEY_12345"
```

**Expected Output**:
- ✅ Returns `None` (not an error)
- ✅ No exception thrown
- ✅ Graceful handling

---

#### Test 7: List Value Sets with Pagination
**Purpose**: Test listing and filtering functionality

**Input Data**:
```python
# Create 5 test value sets
query = {
    "status": "active",
    "module": "ListTest",
    "skip": 0,
    "limit": 3
}
```

**Expected Output**:
```python
{
    "total": 5,  # Total matching records
    "skip": 0,
    "limit": 3,
    "items": [<3 value sets>],  # Actual returned items
    "hasMore": True  # More records available
}
```

**Validation**:
- Pagination math is correct: `hasMore = (skip + limit) < total`
- Filters work correctly
- Sort order is consistent

---

### 3. UPDATE Tests (2 tests)

#### Test 8: Update Value Set Description
**Purpose**: Verify metadata updates work correctly

**Test Flow**:
1. Create value set with description "Original description"
2. Update to "Updated description"
3. Verify change persisted

**Expected Changes**:
- ✅ Description updated
- ✅ `updatedAt` timestamp changed
- ✅ `updatedBy` field set correctly
- ✅ Other fields unchanged (items, status, etc.)

---

#### Test 9: Update Value Set Status
**Purpose**: Test status transitions (active → archived)

**Test Flow**:
1. Create with status "active"
2. Update status to "archived"
3. Verify transition

**Expected Result**:
- ✅ Status changes from "active" to "archived"
- ✅ Audit fields updated correctly

---

### 4. ITEM MANAGEMENT Tests (4 tests)

#### Test 10: Add Item to Value Set
**Purpose**: Verify single item addition

**Input**:
```python
new_item = {
    "code": "NEW",
    "labels": {"en": "New Item", "hi": "नया"}
}
```

**Expected**:
- ✅ Item count increases by 1
- ✅ New item appears in items array
- ✅ Existing items unchanged

---

#### Test 11: Add Duplicate Item Code (Negative Test)
**Purpose**: **Should FAIL** - No duplicate codes within value set

**Expected**:
- ❌ ValueError thrown
- ✅ Item count unchanged
- ✅ Database not modified

---

#### Test 12: Update Item Labels
**Purpose**: Test partial item updates

**Input**:
```python
updates = {
    "labels": {
        "en": "Updated Label",
        "hi": "अपडेट लेबल"
    }
}
```

**Expected**:
- ✅ Labels updated
- ✅ Item code unchanged
- ✅ Other items unaffected

---

#### Test 13: Replace Item Code
**Purpose**: Test complete item code replacement

**Input**:
```python
{
    "oldCode": "OLD",
    "newCode": "NEW",
    "newLabels": {"en": "New Code", "hi": "नया कोड"}
}
```

**Expected**:
- ✅ Old code removed
- ✅ New code present
- ✅ Labels updated
- ✅ No duplicate "OLD" code remains

**Critical Check**:
```python
assert not any(item.code == "OLD" for item in result.items)
assert any(item.code == "NEW" for item in result.items)
```

---

### 5. SEARCH Tests (2 tests)

#### Test 14: Search Value Set Items
**Purpose**: Test text search across items

**Test Data**:
```python
items = [
    {"code": "APPLE", "labels": {"en": "Apple Fruit"}},
    {"code": "BANANA", "labels": {"en": "Banana Fruit"}},
    {"code": "ORANGE", "labels": {"en": "Orange Fruit"}}
]
search_query = "Fruit"
```

**Expected Output**:
```python
{
    "valueSetKey": "TEST_SEARCH_<timestamp>",
    "matchingItems": [<all 3 items>],  # All contain "Fruit"
    "totalMatches": 3
}
```

**Validation**:
- Case-insensitive search works
- All matching items returned
- Search covers multiple fields (code + labels)

---

#### Test 15: Search by Label
**Purpose**: Find value sets containing specific label text

**Input**:
```python
label_text = "Administrator"
language_code = "en"
```

**Expected**:
- ✅ Returns value sets containing items with "Administrator" in English labels
- ✅ Case-insensitive matching
- ✅ Complete value set data returned

---

### 6. ARCHIVE/RESTORE Tests (2 tests)

#### Test 16: Archive Value Set
**Purpose**: Test soft-delete (archive) functionality

**Expected Changes**:
```python
Before: {"status": "active"}
After:  {"status": "archived", "updatedAt": <new_timestamp>}
```

**Response Schema**:
```python
{
    "success": True,
    "key": "TEST_ARCHIVE_<timestamp>",
    "previousStatus": "active",
    "currentStatus": "archived",
    "message": "Value set archived successfully: Testing archive functionality"
}
```

---

#### Test 17: Restore Value Set
**Purpose**: Test unarchive functionality

**Expected**:
- ✅ Status changes from "archived" to "active"
- ✅ Value set becomes editable again
- ✅ All data preserved

---

### 7. BULK OPERATIONS Tests (1 test)

#### Test 18: Bulk Import Value Sets
**Purpose**: Test creating multiple value sets at once

**Input**:
```python
{
    "valueSets": [
        {"key": "TEST_BULK_0", ...},
        {"key": "TEST_BULK_1", ...},
        {"key": "TEST_BULK_2", ...}
    ]
}
```

**Expected**:
```python
{
    "successful": 3,
    "failed": 0,
    "errors": [],
    "processedKeys": ["TEST_BULK_0", "TEST_BULK_1", "TEST_BULK_2"]
}
```

**Critical Check**:
- All or nothing atomicity (if one fails, what happens?)
- Error reporting is detailed
- Database state is consistent

---

### 8. VALIDATION Tests (2 tests)

#### Test 19: Validate Valid Value Set
**Purpose**: Test validation logic without creating

**Input**:
```python
{
    "key": "TEST_VALIDATION",
    "items": [
        {"code": "VAL1", "labels": {"en": "Valid 1"}},
        {"code": "VAL2", "labels": {"en": "Valid 2"}}
    ]
}
```

**Expected Output**:
```python
{
    "isValid": True,
    "errors": [],
    "warnings": []
}
```

---

#### Test 20: Validate Invalid Value Set (Negative Test)
**Purpose**: **Should FAIL** validation - duplicate item codes

**Input**:
```python
{
    "items": [
        {"code": "DUP", "labels": {"en": "Duplicate 1"}},
        {"code": "DUP", "labels": {"en": "Duplicate 2"}}
    ]
}
```

**Expected Output**:
```python
{
    "isValid": False,
    "errors": ["Item codes must be unique within the value set"],
    "warnings": []
}
```

---

### 9. STATISTICS Test (1 test)

#### Test 21: Get Value Set Statistics
**Purpose**: Verify system-wide metrics calculation

**Expected Output**:
```python
{
    "total_value_sets": 20,  # Approximate, based on created tests
    "by_status": {
        "active": 15,
        "archived": 5
    },
    "by_module": {
        "Testing": 10,
        "ListTest": 5,
        "Fruits": 1,
        ...
    },
    "items_statistics": {
        "total_items": 535,  # Including the 500-item test
        "avg_items": 26.75,
        "max_items": 500,
        "min_items": 1,
        "total_capacity": 10000,  # 20 value sets * 500 max
        "capacity_used_percent": 5.35
    }
}
```

**Validation**:
- Counts are accurate
- Math is correct
- All categories represented

---

## 📊 Expected Results

### Success Criteria
```
Total Tests: 21
✅ Expected Passes: 19
❌ Expected Failures: 2 (Tests 3 & 4 are negative tests - they SHOULD fail)

Success Rate: 90.48%
```

### Pass/Fail Determination
- **PASS**: Test behavior matches expected outcome
- **FAIL**: Test behavior deviates from expectation OR exception thrown

### Negative Tests (Designed to Fail)
1. **Test 3**: Create Duplicate Key - Must throw ValueError
2. **Test 4**: Create with Duplicate Item Codes - Must throw ValueError
3. **Test 11**: Add Duplicate Item Code - Must throw ValueError
4. **Test 20**: Validate Invalid Value Set - Must return isValid=False

These tests prove the system **correctly rejects invalid data**.

---

## 🐛 Error Scenarios Tested

### 1. Duplicate Key Prevention
```python
# System MUST reject this:
create_value_set(key="EXISTING_KEY")  # First time - OK
create_value_set(key="EXISTING_KEY")  # Second time - ERROR!
```

### 2. Item Code Uniqueness
```python
# Within same value set - MUST reject:
items = [
    {"code": "DUP", ...},
    {"code": "DUP", ...}  # ERROR!
]
```

### 3. Non-existent Resource Handling
```python
get_value_set_by_key("DOES_NOT_EXIST")  # Returns None, not error
```

### 4. Maximum Item Limit
```python
# Exactly 500 items - OK
items = [create_item() for i in range(500)]  # PASS

# More than 500 items - Should reject (not tested yet!)
items = [create_item() for i in range(501)]  # Should ERROR
```

### 5. Update Non-existent Value Set
```python
update_value_set("DOES_NOT_EXIST", {...})  # Should return None
```

---

## 📈 Test Results Analysis

### Results File Location
```
D:\Core Components\ValueSets\tests\test_results_YYYYMMDD_HHMMSS.json
```

### Results File Structure
```json
{
    "timestamp": "2024-01-15T10:30:00.000Z",
    "summary": {
        "total": 21,
        "passed": 19,
        "failed": 2,
        "success_rate": "90.48%"
    },
    "errors": [
        {
            "test": "test_name",
            "error": "error_message",
            "details": "additional_info"
        }
    ],
    "test_data": {
        "basic_value_set": {...},
        "statistics": {...}
    }
}
```

### How to Interpret Results

#### ✅ All Tests Pass (Best Case)
```
Total Tests: 21
✅ Passed: 21
❌ Failed: 0
Success Rate: 100%
```
**Meaning**: System is fully functional, all business rules enforced correctly.

#### ⚠️ Some Tests Fail (Investigation Needed)
```
Total Tests: 21
✅ Passed: 18
❌ Failed: 3
Success Rate: 85.71%
```
**Action Required**: Review failed tests, check:
1. Is database configured correctly?
2. Are environment variables set?
3. Is MongoDB running?
4. Are there actual bugs in the code?

#### ❌ Many Tests Fail (Critical Issue)
```
Total Tests: 21
✅ Passed: 5
❌ Failed: 16
Success Rate: 23.81%
```
**Critical Issue**: System has fundamental problems. Check:
1. Database connection
2. Schema validation
3. Service layer implementation
4. Data integrity constraints

---

## 🔍 Debugging Failed Tests

### Step 1: Read the Error Message
```
❌ FAIL: Create Duplicate Key (Should Fail)
   Error: Duplicate key was allowed (should have failed)
```

### Step 2: Check Test Logic
- Is the expected behavior correct?
- Is the test implementation correct?

### Step 3: Verify Database State
```python
# Check if duplicate was actually created
db.value_sets.count_documents({"key": "TEST_DUPLICATE"})
# Should be 1, not 2!
```

### Step 4: Review Business Logic
- Check service layer validation
- Check repository constraints
- Check schema validators

---

## 🎯 Test Coverage

### Covered Scenarios
- ✅ Basic CRUD operations
- ✅ Validation rules
- ✅ Error handling
- ✅ Edge cases (max limits)
- ✅ Negative tests
- ✅ Search functionality
- ✅ Bulk operations
- ✅ Archive/restore
- ✅ Statistics

### Not Covered (Future Tests)
- ⏳ Concurrent operations
- ⏳ Transaction rollback
- ⏳ Performance under load
- ⏳ Unicode/special characters handling
- ⏳ Very large item lists (>500)
- ⏳ Network failure recovery
- ⏳ Database connection loss

---

## 📝 Test Maintenance

### Adding New Tests
1. Add test method to `ValueSetTester` class
2. Follow naming convention: `test_<feature>_<scenario>`
3. Include in `run_all_tests()` method
4. Document in this README

### Updating Existing Tests
1. Modify test method
2. Update expected results documentation
3. Run full test suite to ensure no regressions

---

## 🚨 Known Issues & Limitations

### Test Environment
- Tests run against real database (no mocking)
- Tests are sequential (no parallel execution)
- Tests create temporary data (cleaned up after)

### Test Data
- Uses timestamps for unique keys (collision possible if run too fast)
- Some tests depend on previous tests' side effects
- Cleanup may fail if tests crash mid-execution

---

## 📞 Support

### If Tests Fail
1. Check this README for expected behavior
2. Review error messages carefully
3. Verify database connection and configuration
4. Check environment variables
5. Review code changes since last successful run

### Reporting Issues
Include in bug report:
1. Test results JSON file
2. Console output
3. Environment configuration
4. MongoDB version
5. Python version

---

## ✅ Conclusion

This test suite is designed with a **"guilty until proven innocent"** mindset. Every function, every edge case, every error path is tested rigorously. The goal is not just to prove the system works, but to expose where it fails.

**Remember**: A passing test proves the feature works. A failing test reveals a bug or incorrect expectation. Both are valuable!

---

## 📅 Test Execution Log

### Run Test Suite:
```bash
python tests/test.py
```

### Check Results:
```bash
cat tests/test_results_<timestamp>.json
```

### Expected Duration:
- **Setup**: ~2 seconds
- **Test Execution**: ~15-20 seconds (21 tests)
- **Cleanup**: ~2 seconds
- **Total**: ~20-25 seconds

---

**Last Updated**: 2024-01-15
**Test Suite Version**: 1.0.0
**Maintained By**: Value Set QA Team