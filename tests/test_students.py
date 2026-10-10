from tests.conftest import login_client
from backend.models.student import Student

def test_students_list(client):
    login_client(client, 'test_admin', 'Admin@123')
    response = client.get('/students/')
    assert response.status_code == 200
    assert b"STU_TEST001" in response.data

def test_student_profile_view(client):
    login_client(client, 'test_admin', 'Admin@123')
    response = client.get('/students/STU_TEST001')
    assert response.status_code == 200
    assert b"Rahul Sharma" in response.data
    assert b"Composite Success Score" in response.data

def test_create_student_admin(client, app):
    login_client(client, 'test_admin', 'Admin@123')
    response = client.post('/students/create', data={
        'student_id': 'STU_NEW002',
        'first_name': 'Anita',
        'last_name': 'Patel',
        'email': 'anita.patel@test.com',
        'department': 'Computer Science & Engineering',
        'academic_year': 1,
        'semester': 1,
        'section': 'B'
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_NEW002').first()
        assert stu is not None
        assert stu.first_name == 'Anita'

def test_student_feedback_eligibility_lock_when_under_75(client):
    login_client(client, 'test_student', 'Student@123')
    response = client.get('/students/STU_TEST001')
    assert response.status_code == 200
    # In initial test fixture, student has 0 attendance sessions, so feedback is locked
    assert b"Feedback Locked" in response.data or b"Criteria" in response.data
