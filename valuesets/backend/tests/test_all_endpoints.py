import asyncio
import httpx
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"
API_URL = f"{BASE_URL}/api/v1"

# Test users with different roles
TEST_USERS = {
    "admin": {"username": "admin", "password": "pass@123", "role": "SystemAdmin"},
    "developer": {"username": "developer1", "password": "pass@123", "role": "Developer"},
    "operator": {"username": "operator1", "password": "pass@123", "role": "Operator"},
    "support": {"username": "support1", "password": "pass@123", "role": "Support"},
    "app": {"username": "app_service", "password": "pass@123", "role": "Application"}
}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(title: str):
    """Print a formatted test header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}[INFO] {message}{Colors.ENDC}")


async def test_health_endpoint():
    """Test health check endpoint"""
    print_test_header("HEALTH CHECK")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print_success(f"Root endpoint: {response.json()}")
            else:
                print_error(f"Root endpoint failed: {response.status_code}")
            
            # Test health endpoint
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print_success(f"Health endpoint: {response.json()}")
            else:
                print_error(f"Health endpoint failed: {response.status_code}")
                
        except Exception as e:
            print_error(f"Health check failed: {e}")
            return False
    
    return True


async def login_user(username: str, password: str) -> Dict[str, Any]:
    """Login a user and return token info"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/auth/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Login failed: {response.text}")


async def test_authentication():
    """Test authentication endpoints"""
    print_test_header("AUTHENTICATION ENDPOINTS")
    
    tokens = {}
    
    for user_key, user_data in TEST_USERS.items():
        try:
            # Test login
            print(f"\nTesting login for {user_data['username']} ({user_data['role']})...")
            result = await login_user(user_data["username"], user_data["password"])
            tokens[user_key] = result["access_token"]
            print_success(f"Login successful for {user_data['username']}")
            print_info(f"  User role: {result['user']['role']}")
            print_info(f"  Token: {result['access_token'][:20]}...")
            
            # Test /me endpoint
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {tokens[user_key]}"}
                response = await client.get(f"{API_URL}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user_info = response.json()
                    print_success(f"  /me endpoint: {user_info['full_name']} ({user_info['role']})")
                else:
                    print_error(f"  /me endpoint failed: {response.status_code}")
            
            # Test /permissions endpoint
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {tokens[user_key]}"}
                response = await client.get(f"{API_URL}/auth/permissions", headers=headers)
                
                if response.status_code == 200:
                    perms = response.json()
                    print_success(f"  Permissions retrieved: {len(perms['permissions'])} permissions")
                    for perm in perms['permissions']:
                        actions = ", ".join(perm['actions']) if perm['actions'] != ["*"] else "ALL"
                        print_info(f"    - {perm['resource']}: {actions}")
                else:
                    print_error(f"  /permissions endpoint failed: {response.status_code}")
                    
        except Exception as e:
            print_error(f"Authentication test failed for {user_data['username']}: {e}")
            tokens[user_key] = None
    
    return tokens


async def test_valuesets_read(tokens: Dict[str, str]):
    """Test ValueSets read endpoints"""
    print_test_header("VALUESETS READ ENDPOINTS")
    
    for user_key, token in tokens.items():
        if not token:
            continue
            
        user = TEST_USERS[user_key]
        print(f"\nTesting read operations for {user['username']} ({user['role']})...")
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test list ValueSets
            response = await client.get(f"{API_URL}/enums", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"  List ValueSets: {len(data)} sets found")
            else:
                print_error(f"  List ValueSets failed: {response.status_code}")
            
            # Test get specific ValueSet
            response = await client.get(f"{API_URL}/enums/errorSeverity", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"  Get ValueSet 'errorSeverity': {len(data['items'])} items")
            else:
                print_error(f"  Get ValueSet failed: {response.status_code}")
            
            # Test bootstrap
            response = await client.get(f"{API_URL}/enums/bootstrap", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"  Bootstrap: {len(data['data'])} sets loaded")
            else:
                print_error(f"  Bootstrap failed: {response.status_code}")


async def test_valuesets_write(tokens: Dict[str, str]):
    """Test ValueSets write endpoints"""
    print_test_header("VALUESETS WRITE ENDPOINTS")
    
    test_valueset = {
        "key": "testEnum",
        "status": "active",
        "description": "Test enum for API testing",
        "items": [
            {"code": "TEST1", "labels": {"en": "Test One"}},
            {"code": "TEST2", "labels": {"en": "Test Two"}}
        ],
        "created_by": "test"
    }
    
    for user_key, token in tokens.items():
        if not token:
            continue
            
        user = TEST_USERS[user_key]
        print(f"\nTesting write operations for {user['username']} ({user['role']})...")
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test create ValueSet
            response = await client.post(
                f"{API_URL}/enums",
                headers=headers,
                json=test_valueset
            )
            
            if response.status_code == 201:
                print_success(f"  Create ValueSet: Allowed for {user['role']}")
                
                # Test update
                update_data = {
                    "description": "Updated description",
                    "items": [
                        {"code": "TEST1", "labels": {"en": "Updated Test One"}},
                        {"code": "TEST3", "labels": {"en": "Test Three"}}
                    ]
                }
                
                response = await client.put(
                    f"{API_URL}/enums/testEnum",
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    print_success(f"  Update ValueSet: Allowed for {user['role']}")
                else:
                    print_error(f"  Update ValueSet: Denied ({response.status_code})")
                
                # Test archive
                response = await client.delete(
                    f"{API_URL}/enums/testEnum",
                    headers=headers
                )
                
                if response.status_code == 204:
                    print_success(f"  Archive ValueSet: Allowed for {user['role']}")
                else:
                    print_error(f"  Archive ValueSet: Denied ({response.status_code})")
                    
            elif response.status_code == 403:
                print_info(f"  Create ValueSet: Denied for {user['role']} (Expected)")
            elif response.status_code == 400 and "already exists" in response.text:
                print_info(f"  Create ValueSet: Already exists (cleaning up...)")
                # Try to delete it
                await client.delete(f"{API_URL}/enums/testEnum", headers=headers)
            else:
                print_error(f"  Create ValueSet: Unexpected error ({response.status_code})")
            
            # Test cache refresh
            response = await client.post(
                f"{API_URL}/enums/cache/refresh",
                headers=headers
            )
            
            if response.status_code == 204:
                print_success(f"  Cache refresh: Allowed for {user['role']}")
            elif response.status_code == 403:
                print_info(f"  Cache refresh: Denied for {user['role']} (Expected)")
            else:
                print_error(f"  Cache refresh: Unexpected error ({response.status_code})")


async def test_permission_verification(tokens: Dict[str, str]):
    """Test permission verification endpoint"""
    print_test_header("PERMISSION VERIFICATION")
    
    test_cases = [
        ("valuesets", "create"),
        ("valuesets", "read"),
        ("users", "create"),
        ("users", "read"),
        ("system", "admin")
    ]
    
    for user_key, token in tokens.items():
        if not token:
            continue
            
        user = TEST_USERS[user_key]
        print(f"\nTesting permissions for {user['username']} ({user['role']})...")
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            
            for resource, action in test_cases:
                response = await client.post(
                    f"{API_URL}/auth/verify-permission",
                    headers=headers,
                    params={"resource": resource, "action": action}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["has_permission"]:
                        print_success(f"  {resource}:{action} - ALLOWED")
                    else:
                        print_info(f"  {resource}:{action} - DENIED")
                else:
                    print_error(f"  {resource}:{action} - Error ({response.status_code})")


async def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("         VALUESETS API COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"{Colors.ENDC}")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=2.0)
            if response.status_code != 200:
                print_error("Server is not responding. Please start the server first.")
                print_info("Run: cd valuesets/backend && python main.py")
                return
    except:
        print_error("Cannot connect to server at http://localhost:8000")
        print_info("Please start the server first: cd valuesets/backend && python main.py")
        return
    
    # Run tests
    health_ok = await test_health_endpoint()
    if not health_ok:
        print_error("Health check failed. Server may not be properly configured.")
        return
    
    tokens = await test_authentication()
    
    if not any(tokens.values()):
        print_error("No users could authenticate. Check database seeding.")
        return
    
    await test_valuesets_read(tokens)
    await test_valuesets_write(tokens)
    await test_permission_verification(tokens)
    
    # Summary
    print_test_header("TEST SUMMARY")
    print_success("All endpoint tests completed!")
    print_info("Tested endpoints:")
    print_info("  - Health & Root endpoints")
    print_info("  - Authentication (login, /me, /permissions)")
    print_info("  - ValueSets read operations (list, get, bootstrap)")
    print_info("  - ValueSets write operations (create, update, delete, cache)")
    print_info("  - Permission verification")
    print_info(f"\nTested with {len(TEST_USERS)} different user roles")


if __name__ == "__main__":
    asyncio.run(main())