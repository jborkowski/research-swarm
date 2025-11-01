#!/usr/bin/env python3
"""
Test script for the Research Swarm API
"""

import requests
import time
import json

def test_api():
    """Test the Research Swarm API"""
    
    # API base URL
    base_url = "http://localhost:8000"
    
    print("Testing Research Swarm API")
    print("=" * 40)
    
    # Test 1: Check if API is running
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✓ API is running")
        else:
            print(f"✗ API returned status code: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ API is not running. Please start the API server.")
        return
    except Exception as e:
        print(f"✗ Error connecting to API: {e}")
        return
    
    # Test 2: Submit an idea
    print("\nSubmitting test idea...")
    idea_data = {
        "idea": "Create a simple calculator app",
        "priority": "medium"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ideas",
            json=idea_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            idea_id = result["idea_id"]
            print(f"✓ Idea submitted successfully")
            print(f"  Idea ID: {idea_id}")
            print(f"  Status: {result['status']}")
            print(f"  Tracking URL: {result['tracking_url']}")
        else:
            print(f"✗ Failed to submit idea: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"✗ Error submitting idea: {e}")
        return
    
    # Test 3: Check idea status
    print("\nChecking idea status...")
    try:
        response = requests.get(f"{base_url}/api/v1/ideas/{idea_id}/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Status check successful")
            print(f"  Status: {status['status']}")
            print(f"  Current Phase: {status['current_phase']}")
            print(f"  Progress: {status['progress_percentage']}%")
        else:
            print(f"✗ Failed to check status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"✗ Error checking status: {e}")
    
    print("\nAPI tests completed!")

if __name__ == "__main__":
    test_api()