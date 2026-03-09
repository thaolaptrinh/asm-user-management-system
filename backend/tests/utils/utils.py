import random
import string


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    """Generate a random email address for testing. Uses shorter format to keep JWT tokens within DB column limits."""
    return f"{random_lower_string()[:12]}@example.com"
