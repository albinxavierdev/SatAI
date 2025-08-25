#!/usr/bin/env python3
"""
Test script for the ISRO Knowledge Base API.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_search_only():
    """Test the search-only endpoint."""
    print("\nTesting search-only endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/search", params={
            "query": "spacecraft",
            "max_results": 3
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search test passed: Found {data['count']} results")
            return True
        else:
            print(f"❌ Search test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search test error: {e}")
        return False

def test_query():
    """Test the main query endpoint."""
    print("\nTesting query endpoint...")
    try:
        payload = {
            "query": "What spacecraft did ISRO launch?",
            "max_results": 3,
            "include_metadata": True
        }
        response = requests.post(f"{BASE_URL}/query", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query test passed")
            print(f"Answer: {data['answer'][:200]}...")
            print(f"Found {len(data['relevant_documents'])} relevant documents")
            return True
        else:
            print(f"❌ Query test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Vedika - ISRO Knowledge Base API")
    print("=" * 50)
    
    # Wait a bit for server to start
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        test_health,
        test_search_only,
        test_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed. Check the server logs.")

if __name__ == "__main__":
    main()
