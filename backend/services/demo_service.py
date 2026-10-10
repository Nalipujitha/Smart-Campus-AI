import os
import secrets
from flask import current_app
from backend.extensions import db
from backend.models.user import User

DEMO_USERNAME = 'demo_evaluator'
DEMO_EMAIL = 'evaluator.demo@smartcampus.edu'
DEMO_FULL_NAME = 'Demo Evaluator (Read-Only)'
DEMO_ROLE = 'Admin'

def get_or_create_demo_user() -> User:
    """
    Idempotently retrieves or provisions the dedicated demo evaluator account.
    Stores password hash securely using Werkzeug generate_password_hash.
    """
    username = current_app.config.get('DEMO_ADMIN_USERNAME', DEMO_USERNAME) if current_app else DEMO_USERNAME
    user = User.query.filter_by(username=username).first()

    if not user:
        # Check if environment specifies a fixed demo password, otherwise generate a secure random one
        demo_pass = os.environ.get('DEMO_ADMIN_PASSWORD') or secrets.token_urlsafe(24)
        user = User(
            username=username,
            email=DEMO_EMAIL,
            full_name=DEMO_FULL_NAME,
            role=DEMO_ROLE,
            department='Institution-wide Evaluation',
            is_active=True,
            must_change_password=False
        )
        user.set_password(demo_pass)
        db.session.add(user)
        db.session.commit()
    elif not user.is_active:
        user.is_active = True
        db.session.commit()

    return user

def is_demo_user(user: User) -> bool:
    """Checks if the given user is the dedicated demo evaluator."""
    if not user:
        return False
    demo_username = current_app.config.get('DEMO_ADMIN_USERNAME', DEMO_USERNAME) if current_app else DEMO_USERNAME
    return user.username == demo_username or 'demo' in (user.username or '').lower()
