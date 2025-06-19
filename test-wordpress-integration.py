#!/usr/bin/env python3
"""
Test WordPress Integration for The 7 Space
"""

import requests
import json
from datetime import datetime

def test_server_health():
    """Test if the automation server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server Health: RUNNING")
            return True
        else:
            print(f"❌ Server Health: Failed ({response.status_code})")
            return False
    except requests.RequestException as e:
        print(f"❌ Server Health: Connection failed - {e}")
        return False

def test_contact_submission():
    """Test contact form submission endpoint"""
    test_contact = {
        "business_entity": "the_7_space",
        "lead_source": "website_contact_form",
        "form_type": "contact_form_7",
        "submission_time": datetime.now().isoformat(),
        "name": "Test User",
        "email": "test@example.com",
        "phone": "555-123-4567",
        "message": "This is a test contact form submission from WordPress integration test.",
        "subject": "Test Contact Form",
        "interest": "gallery_visit",
        "contact_type": "general_inquiry"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/the7space/contacts",
            json=test_contact,
            headers={
                "Authorization": "Bearer the7space_automation_api_key_2024",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Contact Submission: SUCCESS")
            print(f"   Contact ID: {result.get('contact_id')}")
            print(f"   Status: {result.get('status')}")
            return True
        else:
            print(f"❌ Contact Submission: Failed ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Contact Submission: Connection failed - {e}")
        return False

def test_wordpress_api_simulation():
    """Simulate WordPress API call to test authentication"""
    # This simulates what the WordPress plugin would do
    headers = {
        "Authorization": "Bearer the7space_automation_api_key_2024",
        "Content-Type": "application/json",
        "User-Agent": "The7Space-WordPress-Plugin/1.0.0"
    }
    
    try:
        # Test the root endpoint
        response = requests.get("http://localhost:8000/", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ WordPress API Simulation: SUCCESS")
            data = response.json()
            print(f"   Server: {data.get('message')}")
            print(f"   Business Entity: {data.get('business_entity')}")
            return True
        else:
            print(f"❌ WordPress API Simulation: Failed ({response.status_code})")
            return False
            
    except requests.RequestException as e:
        print(f"❌ WordPress API Simulation: Connection failed - {e}")
        return False

def main():
    print("🧪 Testing The 7 Space WordPress Integration")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_server_health():
        tests_passed += 1
    
    if test_wordpress_api_simulation():
        tests_passed += 1
        
    if test_contact_submission():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("\n📋 Next Steps:")
        print("1. Update WordPress plugin settings with server URL")
        print("2. Test contact form on the7space.com website")
        print("3. Verify contact submissions appear in server logs")
    else:
        print("⚠️  Some tests failed. Check server configuration.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()
