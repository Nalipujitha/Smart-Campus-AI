import re
import time
import secrets
from collections import defaultdict
from threading import Lock
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Thread-safe in-memory login attempt tracker for rate limiting / brute-force protection
_lock = Lock()
_login_failures = defaultdict(list) # key -> list of failure timestamps
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW_SECONDS = 600 # 10 minutes


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Enforces enterprise password strength:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one numerical digit (0-9)."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?~`]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)."
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    Validates username format: 3-30 characters, alphanumeric, underscores, dots.
    """
    if not username or len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters."
    if not re.match(r'^[a-zA-Z0-9_.]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and dots."
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates standard email format.
    """
    if not email or len(email) > 120:
        return False, "Email address is required and cannot exceed 120 characters."
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email.strip()):
        return False, "Please provide a valid email address."
    return True, ""


def validate_student_id(student_id: str) -> tuple[bool, str]:
    """
    Validates student ID format (e.g. STU2024001, 2024CS001, etc.).
    """
    if not student_id or len(student_id) < 3 or len(student_id) > 32:
        return False, "Student ID must be between 3 and 32 characters."
    if not re.match(r'^[a-zA-Z0-9_-]+$', student_id.strip()):
        return False, "Student ID can only contain letters, numbers, hyphens, and underscores."
    return True, ""


def generate_password_reset_token(user_id: int, email: str, secret_key: str) -> str:
    """
    Generates a cryptographically signed, timestamped password reset token.
    """
    serializer = URLSafeTimedSerializer(secret_key, salt='password-reset-salt')
    return serializer.dumps({'user_id': user_id, 'email': email})


def verify_password_reset_token(token: str, secret_key: str, max_age: int = 3600) -> tuple[int | None, str | None]:
    """
    Verifies the reset token signature and checks if it expired (default 1 hour).
    Returns (user_id, email) or (None, None).
    """
    serializer = URLSafeTimedSerializer(secret_key, salt='password-reset-salt')
    try:
        data = serializer.loads(token, max_age=max_age)
        return data.get('user_id'), data.get('email')
    except (SignatureExpired, BadSignature, Exception):
        return None, None


def check_login_rate_limit(identifier: str, ip_address: str = '') -> tuple[bool, int]:
    """
    Checks if login attempts for an identifier or IP exceed lockout threshold.
    Returns (is_allowed, remaining_cooldown_seconds).
    """
    now = time.time()
    key = f"{identifier.strip().lower()}:{ip_address.strip()}"
    with _lock:
        # Clean older than window
        timestamps = [t for t in _login_failures[key] if now - t < LOCKOUT_WINDOW_SECONDS]
        _login_failures[key] = timestamps
        if len(timestamps) >= LOCKOUT_THRESHOLD:
            oldest_relevant = timestamps[0]
            remaining = int(LOCKOUT_WINDOW_SECONDS - (now - oldest_relevant))
            return False, max(1, remaining)
        return True, 0


def record_login_failure(identifier: str, ip_address: str = '') -> None:
    """
    Records a failed login attempt for rate limiting.
    """
    now = time.time()
    key = f"{identifier.strip().lower()}:{ip_address.strip()}"
    with _lock:
        _login_failures[key].append(now)


def reset_login_failures(identifier: str, ip_address: str = '') -> None:
    """
    Clears failure history upon successful login.
    """
    key = f"{identifier.strip().lower()}:{ip_address.strip()}"
    with _lock:
        if key in _login_failures:
            del _login_failures[key]


def generate_csrf_token() -> str:
    """Generates a secure random 32-byte hex token."""
    return secrets.token_hex(32)
