import pytest
from tests.conftest import login_client
from backend.models.user import User
from backend.extensions import db

def test_login_pages_render_distinct_designs(client):
    """Verify all 4 dedicated login pages render with their distinct headings and designs."""
    # 1. Student Login
    resp = client.get('/student/login')
    assert resp.status_code == 200
    assert b"Student Portal" in resp.data
    assert b"Sign in to track your academic journey" in resp.data
    assert b"stu_rahul" in resp.data

    # 2. Admin Login
    resp = client.get('/admin/login')
    assert resp.status_code == 200
    assert b"Administrator Login" in resp.data
    assert b"Manage campus operations and institutional insights" in resp.data
    assert b"admin" in resp.data

    # 3. Faculty Login
    resp = client.get('/faculty/login')
    assert resp.status_code == 200
    assert b"Faculty Portal" in resp.data
    assert b"Manage classes, attendance, and student progress" in resp.data
    assert b"dr.sharma" in resp.data

    # 4. Placement Login
    resp = client.get('/placement/login')
    assert resp.status_code == 200
    assert b"Placement Officer Portal" in resp.data
    assert b"Manage recruitment, student readiness, and placement outcomes" in resp.data
    assert b"placement_officer" in resp.data

    # 5. Gateway Landing
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b"Institutional Portal Gateway" in resp.data


def test_student_login_success_and_redirect(client):
    """Verify student logs in at /student/login and redirects to /student/dashboard."""
    resp = client.post('/student/login', data={
        'username': 'test_student',
        'password': 'Student@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data or b"Rahul" in resp.data
    client.get('/logout')


def test_admin_login_success_and_redirect(client):
    """Verify admin logs in at /admin/login and redirects to /admin/dashboard."""
    resp = client.post('/admin/login', data={
        'username': 'test_admin',
        'password': 'Admin@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Institutional Command Center" in resp.data or b"Admin Control Active" in resp.data
    client.get('/logout')


def test_faculty_login_success_and_redirect(client):
    """Verify faculty logs in at /faculty/login and redirects to /faculty/dashboard."""
    resp = client.post('/faculty/login', data={
        'username': 'test_faculty',
        'password': 'Faculty@123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Faculty Teaching &amp; Mentorship Hub" in resp.data or b"Faculty Teaching" in resp.data
    client.get('/logout')


def test_placement_login_success_and_redirect(client):
    """Verify placement officer logs in at /placement/login and redirects to /placement/dashboard."""
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
        assert resp.status_code == 401 or b"Invalid" in resp.data or b"disabled" in resp.data


def test_authenticated_user_accessing_different_login_page(client):
    """Verify authenticated users are redirected to their own dashboard when visiting another login page."""
    # Log in as student
    client.post('/student/login', data={'username': 'test_student', 'password': 'Student@123'})
    
    # Student visits /admin/login -> redirected to student dashboard
    resp = client.get('/admin/login', follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data or b"Rahul" in resp.data
    
    client.get('/logout')


def test_logout_clears_session_and_redirects(client):
    """Verify logout terminates session and redirects to portal login."""
    client.post('/admin/login', data={'username': 'test_admin', 'password': 'Admin@123'})
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b"Administrator Login" in resp.data or b"Sign in" in resp.data

    # Ensure admin dashboard is now inaccessible without auth
    dash_resp = client.get('/admin/dashboard', follow_redirects=False)
    assert dash_resp.status_code == 302
