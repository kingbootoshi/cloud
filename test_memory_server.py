#!/usr/bin/env python3

import os
import json
import uuid
import requests
from datetime import datetime
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("CLOUD_API_KEY")
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on a different port
HEADERS = {"X-Password": API_KEY}

# Initialize log file
LOG_FILE = f"memory_server_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def log_to_file(message: str):
    """Write a message to the log file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"\n[{timestamp}] {message}\n")

def make_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an HTTP request and return the response"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        else:
            response = requests.post(url, json=data, headers=HEADERS)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def run_all_tests():
    """Execute all API endpoint tests"""
    # Test data
    test_agent_id = "test_agent"
    test_run_id = "test_run"
    test_user_id = "test_user"
    test_memory_id = None  # Will be set after adding memory

    # List of all tests to run
    tests = [
        {
            "name": "Ping Test",
            "endpoint": "ping",
            "method": "GET"
        },
        {
            "name": "Add Memory",
            "endpoint": "add",
            "method": "POST",
            "data": {
                "memories": "This is a test memory",
                "agent_id": test_agent_id,
                "run_id": test_run_id,
                "user_id": test_user_id,
                "metadata": {"test": True},
                "skip_extraction": False,
                "store_mode": "both"
            }
        }
    ]

    # Execute initial tests to get memory ID
    log_to_file("=== MEMORY SERVER TEST EXECUTION ===")
    log_to_file(f"Base URL: {BASE_URL}")
    log_to_file(f"Test Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_to_file("=====================================\n")

    # Execute first two tests and get memory ID
    for test in tests:
        log_to_file(f"=== Executing: {test['name']} ===")
        log_to_file(f"Endpoint: {test['endpoint']}")
        log_to_file(f"Method: {test['method']}")
        
        if 'data' in test:
            log_to_file(f"Request Data: {json.dumps(test['data'], indent=2)}")
        
        response = make_request(
            endpoint=test['endpoint'],
            method=test['method'],
            data=test.get('data')
        )
        
        log_to_file(f"Response: {json.dumps(response, indent=2)}\n")

        # Extract memory ID from add response
        if test['name'] == "Add Memory" and 'result' in response:
            test_memory_id = response['result']['results'][0]['id']

    # Continue with remaining tests using the actual memory ID
    remaining_tests = [
        {
            "name": "Query Memory",
            "endpoint": "query",
            "method": "POST",
            "data": {
                "query": "test memory",
                "agent_id": test_agent_id,
                "run_id": test_run_id,
                "user_id": test_user_id,
                "limit": 5
            }
        },
        {
            "name": "Get All Memories",
            "endpoint": "get_all",
            "method": "POST",
            "data": {
                "agent_id": test_agent_id,
                "run_id": test_run_id,
                "user_id": test_user_id
            }
        },
        {
            "name": "Get Memory by ID",
            "endpoint": "get",
            "method": "POST",
            "data": {
                "memory_id": test_memory_id
            }
        },
        {
            "name": "Update Memory",
            "endpoint": "update",
            "method": "POST",
            "data": {
                "memory_id": test_memory_id,
                "new_data": "Updated test memory"
            }
        },
        {
            "name": "Get Memory History",
            "endpoint": "history",
            "method": "POST",
            "data": {
                "memory_id": test_memory_id
            }
        },
        {
            "name": "Delete Memory",
            "endpoint": "delete",
            "method": "POST",
            "data": {
                "memory_id": test_memory_id
            }
        },
        {
            "name": "Delete All Memories",
            "endpoint": "delete_all",
            "method": "POST",
            "data": {
                "agent_id": test_agent_id,
                "run_id": test_run_id,
                "user_id": test_user_id
            }
        }
    ]

    # Execute remaining tests
    for test in remaining_tests:
        log_to_file(f"=== Executing: {test['name']} ===")
        log_to_file(f"Endpoint: {test['endpoint']}")
        log_to_file(f"Method: {test['method']}")
        
        if 'data' in test:
            log_to_file(f"Request Data: {json.dumps(test['data'], indent=2)}")
        
        response = make_request(
            endpoint=test['endpoint'],
            method=test['method'],
            data=test.get('data')
        )
        
        log_to_file(f"Response: {json.dumps(response, indent=2)}\n")

    # Final cleanup - Reset the memory store
    log_to_file("=== Executing: Reset Memory Store ===")
    reset_response = make_request("reset", method="POST")
    log_to_file(f"Reset Response: {json.dumps(reset_response, indent=2)}\n")

    log_to_file("=== TEST EXECUTION COMPLETED ===")
    log_to_file(f"Test Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_to_file("==============================")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    print(f"Starting memory server tests...")
    print(f"Results will be saved to: {LOG_FILE}")
    
    run_all_tests()
    
    print(f"Tests completed. Check {LOG_FILE} for detailed results.") 