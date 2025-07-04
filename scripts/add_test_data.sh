#!/bin/bash

# This script adds test data, including a user and broker connection details.

# Define user details
USERNAME="ey3locker"
EMAIL="dhinson.dacpano@gmail.com"
PASSWORD="test12345678"

# Define broker connection details
TRADIER_BROKER_ID=1
API_KEY="VA1921000"
API_SECRET="F8ZAWUhT8KxP1fouaTz1jeiqjjbf"


# API endpoints
REGISTER_URL="http://localhost:8000/api/v1/register"
LOGIN_URL="http://localhost:8000/api/v1/token"
BROKER_CONNECTION_URL="http://localhost:8000/api/v1/brokerage_connections"
echo "Starting test data setup..." >&2
echo "Attempting to add user: $USERNAME with email: $EMAIL"

# Send POST request to register user
register_response=$(curl -s -X POST "$REGISTER_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

# Check if user registration was successful
if [ $? -eq 0 ]; then
  if echo "$register_response" | grep -q "detail"; then
    echo "Error during user registration: $(echo "$register_response" | grep -oP '"detail":"\K[^"]*')"
    exit 1
  else
    echo "User '$USERNAME' registered successfully!"
    echo "Response: $register_response"
  fi
else
  echo "Error: Failed to connect to the API or curl command failed during registration."
  echo "Please ensure the FastAPI server is running at http://localhost:8000"
  exit 1
fi

echo "Attempting to log in user: $USERNAME"

# Send POST request to log in and get token
login_response=$(curl -s -X POST "$LOGIN_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

# Check if login was successful and extract token without jq
if [ $? -eq 0 ]; then
  ACCESS_TOKEN=$(echo "$login_response" | grep -oP '"access_token":"\K[^"]*')
  if [ -z "$ACCESS_TOKEN" ]; then
    echo "Error during login: Could not retrieve access token."
    echo "Response: $login_response"
    exit 1
  else
    echo "User '$USERNAME' logged in successfully! Token '$ACCESS_TOKEN' obtained."
  fi
else
  echo "Error: Failed to connect to the API or curl command failed during login."
  echo "Please ensure the FastAPI server is running at http://localhost:8000"
  exit 1
fi

echo "Attempting to add broker connection data for user: $USERNAME"

# Send POST request to add brokerage connection
broker_response=$(curl -s -X POST "$BROKER_CONNECTION_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{
    \"broker_id\": $TRADIER_BROKER_ID,
    \"api_key\": \"$API_KEY\",
    \"api_secret\": \"$API_SECRET\"
  }")

# Check if adding broker connection was successful
if [ $? -eq 0 ]; then
  if echo "$broker_response" | grep -q "detail"; then
    echo "Error adding broker connection: $(echo "$broker_response" | grep -oP '"detail":"\K[^"]*')"
    exit 1
  else
    echo "Broker connection added successfully for user '$USERNAME'!"
    echo "Response: $broker_response"
  fi
else
  echo "Error: Failed to connect to the API or curl command failed during broker connection."
  echo "Please ensure the FastAPI server is running at http://localhost:8000"
  exit 1
fi

echo "Test data setup complete."