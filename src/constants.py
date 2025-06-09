from fastapi import status

# HTTP Status Codes
HTTP_200_OK = status.HTTP_200_OK
HTTP_201_CREATED = status.HTTP_201_CREATED
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND

# Error Messages
USERNAME_ALREADY_REGISTERED = "Username already registered"
EMAIL_ALREADY_REGISTERED = "Email already registered"
INCORRECT_CREDENTIALS = "Incorrect username or password"
BEARER_TOKEN_REQUIRED = "Bearer token required"
INVALID_OR_INACTIVE_REFRESH_TOKEN = "Invalid or inactive refresh token"
INVALID_TOKEN_TYPE = "Invalid token type"
INVALID_TOKEN_PAYLOAD = "Invalid token payload"
USER_NOT_FOUND = "User not found"
COULD_NOT_VALIDATE_REFRESH_TOKEN = "Could not validate refresh token"
ACTIVE_SESSION_NOT_FOUND = "Active session not found"
SESSION_NOT_FOUND_OR_UNAUTHORIZED = "Session not found or not authorized"
BOT_INSTANCE_NOT_FOUND = "Bot instance not found"