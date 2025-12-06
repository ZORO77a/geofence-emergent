import requests
import sys
import json
import time
from datetime import datetime

class GeoCryptAPITester:
    def __init__(self, base_url="https://geocrypt-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.employee_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                try:
                    error_detail = response.json().get('detail', 'No error details')
                    details += f", Error: {error_detail}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_admin_login_flow(self):
        """Test complete admin login flow"""
        print("\n🔐 Testing Admin Login Flow...")
        
        # Step 1: Admin login (should send OTP)
        success, response = self.run_test(
            "Admin Login - Send OTP",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin"}
        )
        
        if not success:
            return False
        
        # Step 2: Mock OTP verification (we'll use a dummy OTP since we can't access email)
        # In real scenario, we'd get OTP from email
        print("    Note: OTP sent to email. Using mock OTP for testing...")
        
        # Try with a dummy OTP first (should fail)
        success, response = self.run_test(
            "Admin OTP Verification - Invalid OTP",
            "POST",
            "auth/verify-otp",
            401,  # Should fail with invalid OTP
            data={"username": "admin", "otp": "123456"}
        )
        
        return True  # Login flow works, OTP verification would work with real OTP

    def test_employee_management(self):
        """Test employee management APIs"""
        print("\n👥 Testing Employee Management...")
        
        if not self.admin_token:
            print("    Skipping - No admin token available")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Create employee
        test_employee = {
            "username": f"test_emp_{int(time.time())}",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "Create Employee",
            "POST",
            "admin/employees",
            200,
            data=test_employee,
            headers=headers
        )
        
        if success:
            # Get employees
            self.run_test(
                "Get Employees List",
                "GET",
                "admin/employees",
                200,
                headers=headers
            )
            
            # Delete employee
            self.run_test(
                "Delete Employee",
                "DELETE",
                f"admin/employees/{test_employee['username']}",
                200,
                headers=headers
            )
        
        return success

    def test_file_management(self):
        """Test file upload and management"""
        print("\n📁 Testing File Management...")
        
        if not self.admin_token:
            print("    Skipping - No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create a test file
        test_content = b"This is a test file for GeoCrypt encryption"
        files = {'file': ('test_file.txt', test_content, 'text/plain')}
        
        success, response = self.run_test(
            "Upload and Encrypt File",
            "POST",
            "files/upload",
            200,
            files=files,
            headers=headers
        )
        
        if success:
            # List files
            self.run_test(
                "List Files",
                "GET",
                "files",
                200,
                headers=headers
            )
        
        return success

    def test_geofence_config(self):
        """Test geofence configuration"""
        print("\n🌍 Testing Geofence Configuration...")
        
        if not self.admin_token:
            print("    Skipping - No admin token available")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        # Get current config
        success, response = self.run_test(
            "Get Geofence Config",
            "GET",
            "admin/geofence-config",
            200,
            headers=headers
        )
        
        if success:
            # Update config
            new_config = {
                "latitude": 10.8505,
                "longitude": 76.2711,
                "radius": 600,
                "allowed_ssid": "TestWiFi",
                "start_time": "08:00",
                "end_time": "18:00"
            }
            
            self.run_test(
                "Update Geofence Config",
                "PUT",
                "admin/geofence-config",
                200,
                data=new_config,
                headers=headers
            )
        
        return success

    def test_access_logs(self):
        """Test access logs retrieval"""
        print("\n📊 Testing Access Logs...")
        
        if not self.admin_token:
            print("    Skipping - No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "Get Access Logs",
            "GET",
            "admin/access-logs",
            200,
            headers=headers
        )
        
        return success

    def test_wfh_requests(self):
        """Test WFH request management"""
        print("\n🏠 Testing WFH Requests...")
        
        if not self.admin_token:
            print("    Skipping - No admin token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        success, response = self.run_test(
            "Get WFH Requests",
            "GET",
            "admin/wfh-requests",
            200,
            headers=headers
        )
        
        return success

    def test_employee_endpoints(self):
        """Test employee-specific endpoints without token"""
        print("\n👤 Testing Employee Endpoints (No Auth)...")
        
        # Test WFH status without token (should fail)
        self.run_test(
            "Get WFH Status - No Auth",
            "GET",
            "wfh-request/status",
            401  # Should fail without authentication
        )
        
        # Test file access without token (should fail)
        self.run_test(
            "Access File - No Auth",
            "POST",
            "files/access",
            401,  # Should fail without authentication
            data={
                "file_id": "dummy_id",
                "latitude": 10.8505,
                "longitude": 76.2711,
                "wifi_ssid": "TestWiFi"
            }
        )

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting GeoCrypt API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200:
                self.log_test("API Server Connectivity", True, "FastAPI docs accessible")
            else:
                self.log_test("API Server Connectivity", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Server Connectivity", False, f"Connection failed: {str(e)}")
            return
        
        # Run test suites
        self.test_admin_login_flow()
        self.test_employee_endpoints()
        
        # Note: Since we can't get real OTP from email in automated testing,
        # we'll skip tests that require authentication tokens
        print("\n⚠️  Note: Authentication-required tests skipped due to OTP email requirement")
        print("    In manual testing, admin would receive OTP via email to complete login")
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"    Total Tests: {self.tests_run}")
        print(f"    Passed: {self.tests_passed}")
        print(f"    Failed: {self.tests_run - self.tests_passed}")
        print(f"    Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = GeoCryptAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'failed_tests': tester.tests_run - tester.tests_passed,
                'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0
            },
            'test_results': tester.test_results,
            'timestamp': datetime.now().isoformat()
        }, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())