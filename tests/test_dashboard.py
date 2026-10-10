from tests.conftest import login_client
from backend.models.user import User
from backend.models.student import Student
from backend.extensions import db

def test_dashboard_requires_login(client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_dashboard_renders_for_admin(client):
    login_client(client, 'test_admin', 'Admin@123')
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"Institutional Command Center" in response.data or b"Total Enrolled" in response.data

def test_dashboard_renders_for_student_role(client, app):
    """Verify that student role renders the redesigned personalized student dashboard."""
    with app.app_context():
        # Create student user if not exists
        stu_user = User.query.filter_by(username='test_student_dash').first()
        if not stu_user:
            stu_user = User(
                username='test_student_dash',
                role='Student',
                student_id='STU2024001',
                full_name='Rahul Verma',
                email='rahul.verma.dash@campus.edu'
            )
            stu_user.set_password('Student@123')
            db.session.add(stu_user)
            db.session.commit()

    login_client(client, 'test_student_dash', 'Student@123')
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back" in response.data or b"Rahul Verma" in response.data
    assert b"Placement Readiness" in response.data
    assert b"Learning Tasks" in response.data
    assert b"Student Success Index" in response.data
