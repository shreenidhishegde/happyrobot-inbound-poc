#!/usr/bin/env python3
"""
Test script for HappyRobot Inbound Carrier Sales Webhook
This script tests the three separate webhook endpoints: verify_mc, load_search, and summary
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "super-secret-happyrobot-key"  # Update this to match your .env file

# Webhook endpoints
VERIFY_MC_URL = f"{BASE_URL}/webhook/happyrobot/verify_mc"
LOAD_SEARCH_URL = f"{BASE_URL}/webhook/happyrobot/load_search"
SUMMARY_URL = f"{BASE_URL}/webhook/happyrobot/summary"

def test_mc_verification():
    """Test MC verification endpoint"""
    
    print("Testing HappyRobot Inbound Carrier Sales Webhook")
    print("=" * 60)
    
    # Test 1: Valid MC number
    print("\n Test 1: Valid MC number verification")
    payload = {
        "conversation_id": "test_conv_001",
        "mc_number": "1515"
    }
    
    response = send_webhook_request(VERIFY_MC_URL, payload)
    print_response(response)
    
    # Assert valid MC verification
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("verified") == True, f"Expected verified=True, got {data.get('verified')}"
    assert "carrier_name" in data, "Expected carrier_name in response"
    assert data.get("say") is not None, "Expected say message in response"
    print("✅ Test 1 PASSED: Valid MC verification")
    
    # Test 2: Invalid MC number
    print("\n❌ Test 2: Invalid MC number verification")
    payload = {
        "conversation_id": "test_conv_002", 
        "mc_number": "INVALID_MC"
    }
    
    response = send_webhook_request(VERIFY_MC_URL, payload)
    print_response(response)
    
    # Assert invalid MC verification
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("verified") == False, f"Expected verified=False, got {data.get('verified')}"
    assert "not eligible" in data.get("say", "").lower(), "Expected rejection message"
    print("✅ Test 2 PASSED: Invalid MC verification")
    
    # Test 3: Missing MC number
    print("\n⚠️ Test 3: Missing MC number")
    payload = {
        "conversation_id": "test_conv_003"
    }
    
    response = send_webhook_request(VERIFY_MC_URL, payload)
    print_response(response)
    
    # Assert missing MC number
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("verified") == False, f"Expected verified=False, got {data.get('verified')}"
    assert "mc number is required" in data.get("message", "").lower(), "Expected MC required message"
    print("✅ Test 3 PASSED: Missing MC number")

def test_load_search():
    """Test load search endpoint"""
    
    print("\n📦 Testing Load Search Endpoint")
    print("=" * 40)
    
    # Test 1: Valid search - Dry Van from Chicago (legacy format)
    print("\n🚛 Test 1: Dry Van from Chicago (legacy format)")
    payload = {
        "equipment_type": "Dry Van",
        "origin": "Chicago",
        "destination": "Dallas",
        "weight_capacity": 15000,
        "available_dates": ["2025-09-10"]
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Assert valid load search
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == True, f"Expected load_found=True, got {data.get('load_found')}"
    assert data.get("status") == "success", f"Expected status=success, got {data.get('status')}"
    assert "load" in data.get("say", "").lower(), "Expected load details in response"
    print("✅ Test 1 PASSED: Valid load search")
    
    # Test 2: Invalid equipment type - TV
    print("\n📺 Test 2: TV equipment (should fail)")
    payload = {
        "equipment_type": "TV",
        "origin": "LA",
        "destination": "Phoenix",
        "weight_capacity": 15000,
        "available_dates": ["2025-09-10"]
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Assert invalid equipment type
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == False, f"Expected load_found=False, got {data.get('load_found')}"
    assert "equipment type not available" in data.get("message", "").lower(), "Expected equipment not available message"
    print("✅ Test 2 PASSED: Invalid equipment type")
    
    # Test 3: Requesting more equipment than available
    print("\n🔢 Test 3: Requesting 5 Dry Vans (should ask about available count)")
    payload = {
        "conversation_id": "test_conv_003",
        "equipment_type": "Dry Van",
        "equipment_count": 5
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Assert insufficient loads
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == False, f"Expected load_found=False, got {data.get('load_found')}"
    assert "insufficient loads available" in data.get("message", "").lower(), "Expected insufficient loads message"
    assert "available_count" in data, "Expected available_count in response"
    print("✅ Test 3 PASSED: Insufficient loads available")
    
    # Test 4: Flatbed from LA (exists but no match)
    print("\n🚛 Test 4: Flatbed from LA (no matching loads)")
    payload = {
        "conversation_id": "test_conv_004",
        "equipment_type": "Flatbed",
        "origin": "LA",
        "equipment_count": 1
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Assert no matching loads
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == False, f"Expected load_found=False, got {data.get('load_found')}"
    assert "no matching loads found" in data.get("message", "").lower(), "Expected no matching loads message"
    print("✅ Test 4 PASSED: No matching loads")

def test_summary_endpoint():
    """Test summary endpoint"""
    
    print("\n📊 Testing Summary Endpoint")
    print("=" * 40)
    
    # Test 1: Successful call summary
    print("\n✅ Test 1: Successful call summary")
    payload = {
        "conversation_id": "test_conv_001",
        "session_id": "session_001",
        "mc_number": "44110",
        "carrier_name": "GREYHOUND LINES INC",
        "load_id": "1",
        "call_outcome": "booked",
        "sentiment": "positive",
        "summary": "Carrier was interested in the load and accepted the rate. Call was successful.",
        "duration": 180
    }
    
    response = send_webhook_request(SUMMARY_URL, payload)
    print_response(response)
    
    # Assert successful summary
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "success", f"Expected status=success, got {data.get('status')}"
    assert "saved successfully" in data.get("message", "").lower(), "Expected success message"
    print("✅ Test 1 PASSED: Successful call summary")
    
    # Test 2: Declined call summary
    print("\n❌ Test 2: Declined call summary")
    payload = {
        "conversation_id": "test_conv_002",
        "session_id": "session_002",
        "mc_number": "44110",
        "carrier_name": "GREYHOUND LINES INC",
        "call_outcome": "declined",
        "sentiment": "negative",
        "summary": "Carrier was not interested in the load due to low rate.",
        "duration": 120
    }
    
    response = send_webhook_request(SUMMARY_URL, payload)
    print_response(response)
    
    # Assert declined summary
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("status") == "success", f"Expected status=success, got {data.get('status')}"
    assert "saved successfully" in data.get("message", "").lower(), "Expected success message"
    print("✅ Test 2 PASSED: Declined call summary")

def test_webhook_security():
    """Test webhook security (missing API key)"""
    print("\n🔒 Test: Missing API key")
    payload = {
        "conversation_id": "test_conv_003",
        "mc_number": "44110"
    }
    
    response = requests.post(VERIFY_MC_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Assert security test
    assert response.status_code == 403, f"Expected 403 (Forbidden), got {response.status_code}"
    assert "invalid api key" in response.text.lower(), "Expected invalid API key message"
    print("✅ Security Test PASSED: Missing API key properly rejected")

def send_webhook_request(url, payload):
    """Send a webhook request with proper headers"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

def print_response(response):
    """Print the webhook response in a formatted way"""
    if response is None:
        print("❌ No response received")
        return
    
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print("Response:")
        print(f"  Say: {data.get('say', 'N/A')}")
        print(f"  Verified: {data.get('verified', 'N/A')}")
        print(f"  Load Found: {data.get('load_found', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
        print(f"  Message: {data.get('message', 'N/A')}")
        if 'carrier_name' in data:
            print(f"  Carrier Name: {data.get('carrier_name', 'N/A')}")
        if 'conversation_id' in data:
            print(f"  Conversation ID: {data.get('conversation_id', 'N/A')}")
    except json.JSONDecodeError:
        print(f"Raw Response: {response.text}")

def test_dashboard_endpoints():
    """Test dashboard endpoints"""
    print("\n📊 Testing Dashboard Endpoints")
    print("=" * 40)
    
    # Test metrics endpoint
    print("\n📈 Testing /dashboard-metrics")
    try:
        response = requests.get(f"{BASE_URL}/dashboard-metrics")
        if response.status_code == 200:
            data = response.json()
            print("✅ Metrics endpoint working")
            print(f"   Total loads: {data.get('total_loads', 'N/A')}")
            print(f"   Total calls: {data.get('total_calls', 'N/A')}")
            print(f"   Success rate: {data.get('success_rate', 'N/A')}%")
            
            # Assert dashboard metrics
            assert isinstance(data.get('total_loads'), int), "Expected total_loads to be integer"
            assert isinstance(data.get('total_calls'), int), "Expected total_calls to be integer"
            assert isinstance(data.get('success_rate'), (int, float)), "Expected success_rate to be number"
            print("✅ Dashboard Metrics Test PASSED")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            assert False, f"Dashboard metrics endpoint failed with status {response.status_code}"
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")
        assert False, f"Dashboard metrics test failed: {e}"
    
    # Test loads endpoint
    print("\n📦 Testing /loads")
    try:
        response = requests.get(f"{BASE_URL}/loads")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Loads endpoint working: {len(data)} loads found")
            
            # Assert loads endpoint
            assert isinstance(data, list), "Expected loads to be a list"
            assert len(data) > 0, "Expected at least one load in database"
            print("✅ Loads Endpoint Test PASSED")
        else:
            print(f"❌ Loads endpoint failed: {response.status_code}")
            assert False, f"Loads endpoint failed with status {response.status_code}"
    except Exception as e:
        print(f"❌ Error testing loads: {e}")
        assert False, f"Loads endpoint test failed: {e}"
    
    # Test dashboard HTML
    print("\n🌐 Testing / (dashboard HTML)")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Dashboard HTML endpoint working")
            
            # Assert dashboard HTML
            assert "text/html" in response.headers.get('content-type', ''), "Expected HTML content type"
            assert len(response.text) > 100, "Expected substantial HTML content"
            print("✅ Dashboard HTML Test PASSED")
        else:
            print(f"❌ Dashboard HTML endpoint failed: {response.status_code}")
            assert False, f"Dashboard HTML endpoint failed with status {response.status_code}"
    except Exception as e:
        print(f"❌ Error testing dashboard HTML: {e}")
        assert False, f"Dashboard HTML test failed: {e}"

def test_carrier_driven_load_search():
    """Test the new carrier-driven load search with multiple dates"""
    print("\n🚛 Testing Carrier-Driven Load Search")
    print("=" * 50)
    
    # Test: Carrier with multiple available dates
    print("\n📅 Test: Carrier with multiple available dates")
    payload = {
        "equipment_type": "Dry Van",
        "origin": "Chicago", 
        "destination": "Dallas",
        "weight_capacity": 15000,
        "available_dates": ["2025-09-10", "2025-09-15", "2025-09-20"]
    }
    
    print(f"Carrier Request: {json.dumps(payload, indent=2)}")
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Assert valid load search
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == True, f"Expected load_found=True, got {data.get('load_found')}"
    assert "best load" in data.get("say", "").lower(), "Expected 'best load' in response"
    assert data.get("total_rate") > 0, "Expected positive total rate"
    print("✅ Test PASSED: Carrier-driven load search with multiple dates")
    
    # Test: Carrier with insufficient weight capacity
    print("\n⚖️ Test: Carrier with insufficient weight capacity")
    payload = {
        "equipment_type": "Dry Van",
        "origin": "Chicago", 
        "destination": "Dallas",
        "weight_capacity": 5000,  # Too low for any loads
        "available_dates": ["2025-09-10"]
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Should find no loads due to weight capacity
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == False, f"Expected load_found=False, got {data.get('load_found')}"
    print("✅ Test PASSED: Weight capacity filtering works")
    
    # Test: Invalid equipment type
    print("\n🚫 Test: Invalid equipment type")
    payload = {
        "equipment_type": "Invalid Equipment",
        "origin": "Chicago", 
        "destination": "Dallas",
        "weight_capacity": 15000,
        "available_dates": ["2025-09-10"]
    }
    
    response = send_webhook_request(LOAD_SEARCH_URL, payload)
    print_response(response)
    
    # Should return equipment not available
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data.get("load_found") == False, f"Expected load_found=False, got {data.get('load_found')}"
    assert "equipment type not available" in data.get("say", "").lower(), "Expected equipment not available message"
    print("✅ Test PASSED: Invalid equipment type handled correctly")

def main():
    """Main test function"""
    print("🧪 HappyRobot Webhook Testing Suite")
    print("Make sure your FastAPI server is running on localhost:8000")
    print("Update the API_KEY variable in this script to match your .env file")
    print("=" * 60)
    
    # Wait for user confirmation
    input("Press Enter to start testing...")
    
    try:
        # Test MC verification
        test_mc_verification()
        
        # Test load search
        test_load_search()
        
        # Test new carrier-driven load search
        test_carrier_driven_load_search()
        
        # Test summary endpoint
        test_summary_endpoint()
        
        # Test security
        test_webhook_security()
        
        # Test dashboard
        test_dashboard_endpoints()
        
        print("\n🎉 Testing completed!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")

if __name__ == "__main__":
    main()
