import pytest
from src.utils.security import hash_password, verify_password

def test_hash_password():
    password = "testpassword"
    hashed = hash_password(password)
    assert len(hashed) > 0
    assert hashed != password
    assert verify_password(password, hashed)

def test_verify_password_correct():
    password = "securepassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    password = "securepassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False

def test_hash_password_invalid_input():
    with pytest.raises(ValueError):
        hash_password("")
    with pytest.raises(ValueError):
        hash_password(None)

def test_verify_password_invalid_input():
    with pytest.raises(ValueError):
        verify_password("", "somehash")
    with pytest.raises(ValueError):
        verify_password("password", "")
    with pytest.raises(ValueError):
        verify_password("password", None)

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