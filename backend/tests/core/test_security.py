from app.core.security import hash_password, verify_password


def test_hash_password_returns_string() -> None:
    """Test that hash_password returns a string."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    assert isinstance(hashed, str)
    assert len(hashed) == 60


def test_verify_password_correct_returns_true() -> None:
    """Test that verifying correct password returns True."""
    password = "CorrectPassword456!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect_returns_false() -> None:
    """Test that verifying incorrect password returns False."""
    password = "OriginalPassword123!"
    hashed = hash_password(password)
    wrong_password = "WrongPassword789!"
    assert verify_password(wrong_password, hashed) is False


def test_verify_password_empty_string_returns_false() -> None:
    """Test that verifying empty string password returns False."""
    password = "ValidPassword456!"
    hashed = hash_password(password)
    assert verify_password("", hashed) is False


def test_hash_same_password_twice_different_hashes() -> None:
    """Test that hashing same password twice produces different hashes (random salt)."""
    password = "SamePassword789!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_hash_password_format() -> None:
    """Test that hashed password has correct bcrypt format."""
    password = "FormatTest123!"
    hashed = hash_password(password)
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60
