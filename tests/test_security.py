import pytest
# Removed direct import of hash_password, verify_password as they are now handled by User model

def test_user_set_and_check_password():
    """Test set_password and check_password methods of User model."""
    from src.models.user import User
    user = User(username="testuser", email="test@example.com")
    password = "securepassword123"
    
    user.set_password(password)
    assert user.hashed_password is not None
    assert user.hashed_password != password
    
    assert user.check_password(password) is True
    assert user.check_password("wrongpassword") is False

def test_user_check_password_empty_password():
    """Test check_password with an empty password."""
    from src.models.user import User
    user = User(username="testuser", email="test@example.com")
    user.set_password("password")
    assert user.check_password("") is False

def test_user_check_password_no_hashed_password():
    """Test check_password when hashed_password is not set."""
    from src.models.user import User
    user = User(username="testuser", email="test@example.com")
    # hashed_password is None or empty
    assert user.check_password("password") is False