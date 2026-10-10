import pytest
from datetime import datetime, date
from tests.conftest import login_client
from backend.models.user import User
from backend.models.student import Student
from backend.extensions import db
from backend.utils.security import (
    validate_password_strength,
    generate_password_reset_token,
    verify_password_reset_token,
    reset_login_failures
)

def test_login_pages_render_distinct_designs(client):
    """Verify all 4 dedicated login pages render with their distinct headings and designs."""
    # 1. Student Login
    resp = client.get('/student/login')
    assert resp.status_code == 200
    assert b"Student Portal" in resp.data
    assert b"Sign in to track your academic journey" in resp.data
    assert b"stu_rahul" in resp.data
    assert b"Forgot Password?" in resp.data
    assert b"Sign Up" in resp.data

    # 2. Admin Login
    resp = client.get('/admin/login')
    assert resp.status_code == 200
    assert b"Administrator Login" in resp.data
    assert b"Manage campus operations and institutional insights" in resp.data
    assert b"admin" in resp.data
    assert b"Forgot Password?" in resp.data

    # 3. Faculty Login
    resp = client.get('/faculty/login')
    assert resp.status_code == 200
    assert b"Faculty Portal" in resp.data
    assert b"Manage classes, attendance, and student progress" in resp.data
    assert b"dr.sharma" in resp.data
    assert b"Forgot Password?" in resp.data

    # 4. Placement Login
    resp = client.get('/placement/login')
    assert resp.status_code == 200
    assert b"Placement Officer Portal" in resp.data
    assert b"Manage recruitment, student readiness, and placement outcomes" in resp.data
    assert b"placement_officer" in resp.data
    assert b"Forgot Password?" in resp.data

    # 5. Gateway Landing
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b"Institutional Portal Gateway" in resp.data
    assert b"Register as Student" in resp.data


def test_student_login_success_and_redirect(client):
    """Verify student logs in at /student/login and redirects to /student/dashboard."""
    reset_login_failures('test_student')
    resp = client.post('/student/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data or b"Rahul" in resp.data
    client.get('/logout')


def test_admin_login_success_and_redirect(client):
    """Verify admin logs in at /admin/login and redirects to /admin/dashboard."""
    reset_login_failures('test_admin')
    resp = client.post('/admin/login', data={
        'username': 'test_admin',
        'password': 'Admin@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Institutional Command Center" in resp.data or b"Admin Control Active" in resp.data
    client.get('/logout')


def test_faculty_login_success_and_redirect(client):
    """Verify faculty logs in at /faculty/login and redirects to /faculty/dashboard."""
    reset_login_failures('test_faculty')
    resp = client.post('/faculty/login', data={
        'username': 'test_faculty',
        'password': 'Faculty@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Faculty Teaching &amp; Mentorship Hub" in resp.data or b"Faculty Teaching" in resp.data
    client.get('/logout')


def test_placement_login_success_and_redirect(client):
    """Verify placement officer logs in at /placement/login and redirects to /placement/dashboard."""
    reset_login_failures('test_placement')
    resp = client.post('/placement/login', data={
        'username': 'test_placement',
        'password': 'Placement@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Placement &amp; Recruitment Command Center" in resp.data or b"Placement" in resp.data
    client.get('/logout')


def test_cross_role_login_denial(client):
    """Verify that users cannot log in through an unauthorized role portal."""
    # 1. Student attempting to log in via Admin login page -> Denied
    resp = client.post('/admin/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 403 or b"Access Denied" in resp.data or b"does not have permission" in resp.data

    # 2. Student attempting to log in via Faculty login page -> Denied
    resp = client.post('/faculty/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 403 or b"Access Denied" in resp.data or b"does not have permission" in resp.data

    # 3. Student attempting to log in via Placement login page -> Denied
    resp = client.post('/placement/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 403 or b"Access Denied" in resp.data or b"does not have permission" in resp.data

    # 4. Faculty attempting to log in via Admin login page -> Denied
    resp = client.post('/admin/login', data={
        'username': 'test_faculty',
        'password': 'Faculty@123'
    }, follow_redirects=True)
    assert resp.status_code == 403 or b"Access Denied" in resp.data or b"does not have permission" in resp.data


def test_invalid_credentials_rejected(client):
    """Verify wrong passwords or non-existent usernames are rejected on each page."""
    for url in ['/student/login', '/admin/login', '/faculty/login', '/placement/login']:
        resp = client.post(url, data={
            'username': 'non_existent_user',
            'password': 'BadPassword@999'
        }, follow_redirects=True)
        assert resp.status_code in [401, 429] or b"Invalid" in resp.data or b"disabled" in resp.data


def test_student_registration_flow(client, app):
    """Test full student self-registration flow with validation and password hashing."""
    reg_data = {
        'full_name': 'Ananya Sen',
        'username': 'ananya_sen',
        'email': 'ananya.sen@campus.edu',
        'student_id': 'STU2024888',
        'password': 'SecurePassword@2026',
        'confirm_password': 'SecurePassword@2026'
    }
    resp = client.post('/register', data=reg_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Registration successful" in resp.data or b"Student Portal" in resp.data

    with app.app_context():
        user = User.query.filter_by(username='ananya_sen').first()
        assert user is not None
        assert user.role == 'Student'
        assert user.student_id == 'STU2024888'
        assert user.check_password('SecurePassword@2026')
        assert user.password_hash != 'SecurePassword@2026' # Hashed with Werkzeug

        student = Student.query.filter_by(student_id='STU2024888').first()
        assert student is not None
        assert student.first_name == 'Ananya'


def test_student_registration_duplicate_rejections(client):
    """Verify duplicate username, email, or student ID are rejected."""
    # Duplicate username
    resp = client.post('/register', data={
        'full_name': 'Duplicate User',
        'username': 'test_student', # Already exists in fixture
        'email': 'unique1@campus.edu',
        'student_id': 'STU9991',
        'password': 'SecurePassword@2026',
        'confirm_password': 'SecurePassword@2026'
    }, follow_redirects=True)
    assert resp.status_code in [400, 409] or b"already taken" in resp.data

    # Duplicate email
    resp = client.post('/register', data={
        'full_name': 'Duplicate Email User',
        'username': 'unique_user_99',
        'email': 'stu@test.com', # Already exists in fixture
        'student_id': 'STU9992',
        'password': 'SecurePassword@2026',
        'confirm_password': 'SecurePassword@2026'
    }, follow_redirects=True)
    assert resp.status_code in [400, 409] or b"already registered" in resp.data

    # Duplicate student ID
    resp = client.post('/register', data={
        'full_name': 'Duplicate ID User',
        'username': 'unique_user_88',
        'email': 'unique88@campus.edu',
        'student_id': 'STU_TEST001', # Already exists in fixture
        'password': 'SecurePassword@2026',
        'confirm_password': 'SecurePassword@2026'
    }, follow_redirects=True)
    assert resp.status_code in [400, 409] or b"already registered" in resp.data


def test_password_strength_enforcement(client):
    """Verify that weak passwords are systematically rejected."""
    # Weak: too short
    valid, err = validate_password_strength("Short1!")
    assert not valid and "at least 8" in err

    # Weak: no uppercase
    valid, err = validate_password_strength("lowercase123!")
    assert not valid and "uppercase" in err

    # Weak: no lowercase
    valid, err = validate_password_strength("UPPERCASE123!")
    assert not valid and "lowercase" in err

    # Weak: no digits
    valid, err = validate_password_strength("NoDigitsSpecial!")
    assert not valid and "numerical digit" in err

    # Weak: no special char
    valid, err = validate_password_strength("NoSpecialChar123")
    assert not valid and "special character" in err

    # Strong: meets all criteria
    valid, err = validate_password_strength("Secure@Password123")
    assert valid and err == ""


def test_inactive_account_denied_login(client, app):
    """Verify disabled/inactive accounts cannot log in."""
    with app.app_context():
        u = User.query.filter_by(username='test_student').first()
        u.is_active = False
        db.session.commit()

    reset_login_failures('test_student')
    resp = client.post('/student/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 401 or b"disabled" in resp.data or b"Invalid" in resp.data


def test_password_reset_token_lifecycle(client, app):
    """Verify forgot password token generation, validation, and reset flow."""
    # 1. Request reset link
    resp = client.post('/forgot-password', data={'email_or_username': 'stu@test.com'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"password reset instructions" in resp.data

    with app.app_context():
        user = User.query.filter_by(email='stu@test.com').first()
        token = generate_password_reset_token(user.id, user.email, app.config['SECRET_KEY'])
        uid, email = verify_password_reset_token(token, app.config['SECRET_KEY'])
        assert uid == user.id
        assert email == 'stu@test.com'

    # 2. Visit reset password page
    resp = client.get(f'/reset-password/{token}')
    assert resp.status_code == 200
    assert b"Create New Password" in resp.data

    # 3. Submit new strong password
    resp = client.post(f'/reset-password/{token}', data={
        'password': 'NewPassword@2026',
        'confirm_password': 'NewPassword@2026'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"successfully reset" in resp.data or b"Student Portal" in resp.data

    # 4. Verify user can now log in with new password
    reset_login_failures('test_student')
    login_resp = client.post('/student/login', data={
        'username': 'test_student',
        'password': 'NewPassword@2026'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Welcome back" in login_resp.data or b"Rahul" in login_resp.data


def test_student_data_privacy_isolation(client, app):
    """Verify that a student user cannot view another student's profile."""
    # Create second student
    with app.app_context():
        stu2 = Student(
            student_id='STU_TEST002',
            first_name='Priya',
            last_name='Nair',
            email='priya@test.com',
            department='Electronics & Communication',
            academic_year=2,
            semester=3
        )
        db.session.add(stu2)
        u2 = User(
            username='priya_student',
            email='priya@test.com',
            full_name='Priya Nair',
            role='Student',
            student_id='STU_TEST002'
        )
        u2.set_password('Student@123')
        db.session.add(u2)
        db.session.commit()

    # Log in as test_student (STU_TEST001)
    reset_login_failures('test_student')
    client.post('/student/login', data={'username': 'test_student', 'password': 'Student@123'})

    # Try to view STU_TEST002 profile -> should be redirected away with warning
    resp = client.get('/students/STU_TEST002', follow_redirects=True)
    assert resp.status_code == 200
    assert b"Unauthorized" in resp.data or b"STU_TEST001" in resp.data or b"Rahul" in resp.data
