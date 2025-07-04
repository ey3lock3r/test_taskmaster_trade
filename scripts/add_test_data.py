import requests
import json
import sys

# This script adds test data, including a user and broker connection details.

# Define API endpoints
REGISTER_URL = "http://localhost:8000/api/v1/register"
LOGIN_URL = "http://localhost:8000/api/v1/token"
BROKER_CONNECTION_URL = "http://localhost:8000/api/v1/brokerage_connections"

def add_test_data(username, email, password, api_key, api_secret):
    """
    Adds a test user and broker connection data to the system.
    """
    # 1. Register User
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    headers = {"Content-Type": "application/json"}

    print(f"Attempting to register user: {username} with email: {email}")
    try:
        register_response = requests.post(REGISTER_URL, data=json.dumps(user_data), headers=headers)
        register_response.raise_for_status()
        print(f"User '{username}' registered successfully!")
        print("Response:")
        print(json.dumps(register_response.json(), indent=4))
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during registration: {http_err}")
        print(f"Response content: {register_response.text}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error during registration: {conn_err}")
        print("Please ensure the FastAPI server is running at http://localhost:8000")
        sys.exit(1)
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred during registration: {req_err}")
        sys.exit(1)

    # 2. Log in User and Get Token
    login_data = {
        "email": email,
        "password": password
    }
    login_headers = {"Content-Type": "application/json"}

    print(f"Attempting to log in user: {username}")
    try:
        login_response = requests.post(LOGIN_URL, json=login_data, headers=login_headers)
        login_response.raise_for_status()
        access_token = login_response.json().get("access_token")
        if not access_token:
            print("Error during login: Could not retrieve access token.")
            print(f"Response content: {login_response.text}")
            sys.exit(1)
        print(f"User '{username}' logged in successfully! Token obtained.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error during login: {http_err}")
        print(f"Response content: {login_response.text}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error during login: {conn_err}")
        print("Please ensure the FastAPI server is running at http://localhost:8000")
        sys.exit(1)
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred during login: {req_err}")
        sys.exit(1)

    # 3. Add Broker Connection Data
    broker_data = {
        "broker_id": 1, # Hardcoded broker_id to 1
        "api_key": api_key,
        "api_secret": api_secret
    }
    broker_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    print(f"Attempting to add broker connection data for user: {username}")
    try:
        broker_response = requests.post(BROKER_CONNECTION_URL, json=broker_data, headers=broker_headers)
        broker_response.raise_for_status()
        print(f"Broker connection added successfully for user '{username}'!")
        print("Response:")
        print(json.dumps(broker_response.json(), indent=4))
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error adding broker connection: {http_err}")
        print(f"Response content: {broker_response.text}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error adding broker connection: {conn_err}")
        print("Please ensure the FastAPI server is running at http://localhost:8000")
        sys.exit(1)
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred adding broker connection: {req_err}")
        sys.exit(1)

    print("Test data setup complete.")

if __name__ == "__main__":
    # User details
    test_username = "ey3locker"
    test_email = "dhinson.dacpano@gmail.com"
    test_password = "test12345678"

    # Broker connection details
    test_api_key = "VA1921000"
    test_api_secret = "F8ZAWUhT8KxP1fouaTz1jeiqjjbf"

    add_test_data(test_username, test_email, test_password, test_api_key, test_api_secret)