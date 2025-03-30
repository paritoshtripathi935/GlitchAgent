import asyncio
import os
import json
import base64
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# API endpoint
BASE_URL = "http://localhost:8000/v1/glitch-agent"

async def test_github_login_search():
    """Test GitHub login and search flow"""
    print("Testing GitHub login and search flow...")
    
    # Replace with your GitHub credentials
    # For demo purposes, you can use placeholders
    credentials = {
        "username": "your_github_username",
        "password": "your_github_password"
    }
    
    # Step 1: Login to GitHub
    command_request = {
        "command": "Login to GitHub",
        "context": "I want to log in to GitHub using my credentials",
        "credentials": credentials
    }
    
    response = requests.post(f"{BASE_URL}/command", json=command_request)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    command_response = response.json()
    request_id = command_response.get("request_id")
    
    print(f"Command processed. Request ID: {request_id}")
    print(f"Actions to execute: {json.dumps(command_response.get('actions'), indent=2)}")
    
    # Wait for execution to complete
    print("Waiting for execution to complete...")
    await wait_for_execution(request_id)
    
    # Step 2: Search for a repository
    command_request = {
        "command": "Search for 'playwright python' on GitHub",
        "context": "I want to find repositories related to Playwright for Python"
    }
    
    response = requests.post(f"{BASE_URL}/command", json=command_request)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    command_response = response.json()
    request_id = command_response.get("request_id")
    
    print(f"Command processed. Request ID: {request_id}")
    print(f"Actions to execute: {json.dumps(command_response.get('actions'), indent=2)}")
    
    # Wait for execution to complete
    print("Waiting for execution to complete...")
    await wait_for_execution(request_id)
    
    # Step 3: Click on the first search result
    command_request = {
        "command": "Click on the first search result",
        "context": "I want to open the first repository from the search results"
    }
    
    response = requests.post(f"{BASE_URL}/command", json=command_request)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    command_response = response.json()
    request_id = command_response.get("request_id")
    
    print(f"Command processed. Request ID: {request_id}")
    print(f"Actions to execute: {json.dumps(command_response.get('actions'), indent=2)}")
    
    # Wait for execution to complete
    print("Waiting for execution to complete...")
    await wait_for_execution(request_id)
    
    # Stop the browser
    print("Stopping browser...")
    requests.post(f"{BASE_URL}/stop-browser")
    
    print("Test completed successfully!")


async def wait_for_execution(request_id, max_retries=30, delay=1):
    """Wait for execution to complete and display the result"""
    retries = 0
    while retries < max_retries:
        response = requests.get(f"{BASE_URL}/execution/{request_id}")
        if response.status_code != 200:
            print(f"Error checking execution status: {response.text}")
            return
        
        result = response.json()
        if result.get("message") != "Execution is still in progress":
            print(f"Execution completed: {result.get('message')}")
            
            # If there's a screenshot, save it
            if result.get("screenshot"):
                screenshot_data = base64.b64decode(result.get("screenshot"))
                with open(f"screenshot_{request_id}.png", "wb") as f:
                    f.write(screenshot_data)
                print(f"Screenshot saved as screenshot_{request_id}.png")
            
            if result.get("error"):
                print(f"Error during execution: {result.get('error')}")
            
            return
        
        retries += 1
        await asyncio.sleep(delay)
    
    print("Execution timed out")


if __name__ == "__main__":
    asyncio.run(test_github_login_search())
