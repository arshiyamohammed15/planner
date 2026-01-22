#!/usr/bin/env python3

import requests

# Test the server
def test_server():
    base_url = "http://localhost:8080"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtayIsImlhdCI6MTc2OTA4NTQxMywiZXhwIjoxNzY5MDg5MDEzfQ.yPTlrJiHozhXkwnB56oh6EcYR8YLEUpRfnhnr0-npYY"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health failed: {e}")

    # Test tasks endpoint
    print("\nTesting tasks endpoint...")
    try:
        response = requests.get(f"{base_url}/tasks", headers=headers)
        print(f"Tasks: {response.status_code}")
        if response.status_code == 200:
            tasks = response.json()
            print(f"Found {len(tasks)} tasks")
            if tasks:
                task_id = tasks[0]['id']
                print(f"First task ID: {task_id}")

                # Test task details endpoint
                print(f"\nTesting task details for {task_id}...")
                response = requests.get(f"{base_url}/tasks/{task_id}", headers=headers)
                print(f"Task details: {response.status_code}")
                if response.status_code == 200:
                    task_data = response.json()
                    print(f"Task: {task_data.get('id')} - {task_data.get('description', '')[:50]}...")
        else:
            print(f"Tasks response: {response.text}")
    except Exception as e:
        print(f"Tasks failed: {e}")

    # Test frontend serving
    print("\nTesting frontend serving...")
    try:
        response = requests.get(f"{base_url}/frontend/task_page_example.html")
        print(f"Frontend: {response.status_code}")
        if response.status_code == 200:
            print("Frontend HTML served successfully")
        else:
            print(f"Frontend failed: {response.text}")
    except Exception as e:
        print(f"Frontend failed: {e}")

if __name__ == "__main__":
    test_server()