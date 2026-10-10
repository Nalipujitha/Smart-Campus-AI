import pytest
from flask import session
from backend.models.user import User
from backend.services.demo_service import get_or_create_demo_user, is_demo_user

def test_demo_login_button_rendered_when_enabled(client, app):
    """Verify Demo Login button appears on login page when DEMO_LOGIN_ENABLED is True."""
    app.config['DEMO_LOGIN_ENABLED'] = True
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Demo Login" in response.data
    assert b"demo-login-btn" in response.data

def test_demo_login_button_hidden_when_disabled(client, app):
    """Verify Demo Login button is omitted when DEMO_LOGIN_ENABLED is False."""
    app.config['DEMO_LOGIN_ENABLED'] = False
    response = client.get('/login')
    assert response.status_code == 200
    assert b"demo-login-btn" not in response.data

def test_demo_login_success_and_session(client, app):
    """Verify clicking Demo Login provisions evaluator account and grants admin dashboard access."""
    app.config['DEMO_LOGIN_ENABLED'] = True
    response = client.post('/demo-login', follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Evaluator!" in response.data or b"Institutional Command Center" in response.data
    
    with client.session_transaction() as sess:
        assert sess.get('username') == 'demo_evaluator'
        assert sess.get('role') == 'Admin'
        assert sess.get('is_demo') is True

def test_demo_login_disabled_rejection(client, app):
    """Verify /demo-login returns 403 / redirect when DEMO_LOGIN_ENABLED is False."""
    app.config['DEMO_LOGIN_ENABLED'] = False
    response = client.post('/demo-login', follow_redirects=True)
    assert b"Demo login is currently disabled" in response.data

def test_demo_account_password_securely_hashed(app):
    """Verify demo evaluator password is stored exclusively as a secure cryptographic hash."""
    with app.app_context():
        user = get_or_create_demo_user()
        assert user.password_hash is not None
        assert len(user.password_hash) > 20
        assert not user.password_hash.startswith("password")
        assert not user.password_hash.startswith("Admin")
        # Werkzeug standard hashing schemes
        assert any(user.password_hash.startswith(prefix) for prefix in ['pbkdf2:sha256:', 'scrypt:', 'argon2:'])

def test_demo_account_idempotent_creation(app):
    """Verify repeated execution does not duplicate demo accounts."""
    with app.app_context():
        user1 = get_or_create_demo_user()
        user2 = get_or_create_demo_user()
        assert user1.id == user2.id
        demo_count = User.query.filter_by(username='demo_evaluator').count()
        assert demo_count == 1

def test_demo_evaluator_restricted_from_deleting_users(client, app):
    """Verify demo evaluator cannot delete user accounts."""
    app.config['DEMO_LOGIN_ENABLED'] = True
    # Log in via demo login
    client.post('/demo-login', follow_redirects=True)
    
    with app.app_context():
        target_user = User.query.filter_by(username='test_faculty').first()
        target_id = target_user.id

    # Attempt delete
    resp = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)
    assert b"Action disabled in Demo Mode" in resp.data

    with app.app_context():
        still_exists = User.query.get(target_id)
        assert still_exists is not None

def test_demo_evaluator_restricted_from_resetting_passwords(client, app):
    """Verify demo evaluator cannot reset passwords of other users."""
    app.config['DEMO_LOGIN_ENABLED'] = True
    client.post('/demo-login', follow_redirects=True)
    
    with app.app_context():
        target_user = User.query.filter_by(username='test_faculty').first()
        target_id = target_user.id
        old_hash = target_user.password_hash

    # Attempt password reset
    resp = client.post(f'/admin/users/{target_id}/reset-password', data={'new_password': 'NewPassword@123'}, follow_redirects=True)
    assert b"Action disabled in Demo Mode" in resp.data

    with app.app_context():
        user_after = User.query.get(target_id)
        assert user_after.password_hash == old_hash

def test_demo_evaluator_restricted_from_modifying_weights(client, app):
    """Verify demo evaluator cannot alter institutional scoring weights."""
    app.config['DEMO_LOGIN_ENABLED'] = True
    client.post('/demo-login', follow_redirects=True)

    resp = client.post('/admin/settings/update-weights', data={
        'weight_academic': '0.50',
        'weight_attendance': '0.50',
        'weight_lms': '0.0',
        'weight_engagement': '0.0',
        'weight_placement': '0.0',
        'weight_skills': '0.0',
        'weight_feedback': '0.0'
    }, follow_redirects=True)
    assert b"Action disabled in Demo Mode" in resp.data

def test_demo_cli_command(runner):
    """Verify init-demo-account CLI command works seamlessly."""
    result = runner.invoke(args=['init-demo-account'])
    assert result.exit_code == 0
    assert "Demo Evaluator account" in result.output
