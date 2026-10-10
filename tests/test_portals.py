import pytest
from datetime import date
from tests.conftest import login_client
from backend.models.user import User
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.academic import SubjectScore
from backend.models.intervention import Intervention
from backend.models.placement import Company, JobOpportunity, JobApplication, PlacementOffer, PlacementProfile
from backend.extensions import db

def test_login_redirection_for_all_roles(client):
    """Verify that each role is redirected to its dedicated dashboard upon login."""
    # 1. Admin -> /admin/dashboard
    resp = login_client(client, 'test_admin', 'Admin@123')
    assert resp.status_code == 200
    assert b"Institutional Command Center" in resp.data
    client.get('/logout')

    # 2. Faculty -> /faculty/dashboard
    resp = login_client(client, 'test_faculty', 'Faculty@123')
    assert resp.status_code == 200
    assert b"Faculty Teaching &amp; Mentorship Hub" in resp.data or b"Faculty Teaching" in resp.data
    client.get('/logout')

    # 3. Placement Officer -> /placement/dashboard
    resp = login_client(client, 'test_placement', 'Placement@123')
    assert resp.status_code == 200
    assert b"Placement &amp; Recruitment Command Center" in resp.data or b"Placement" in resp.data
    client.get('/logout')

    # 4. Student -> /student/dashboard
    resp = login_client(client, 'test_student', 'Student@123')
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data
    client.get('/logout')


def test_role_based_access_controls_denial(client):
    """Verify that unauthorized roles cannot access protected portals."""
    # Student attempts to access admin portal -> 403 Access Denied
    login_client(client, 'test_student', 'Student@123')
    resp = client.get('/admin/dashboard')
    assert resp.status_code == 403 or b"Access Denied" in resp.data or resp.status_code == 302
    
    # Student attempts to access faculty portal -> 403 Access Denied
    resp = client.get('/faculty/dashboard')
    assert resp.status_code == 403 or b"Access Denied" in resp.data or resp.status_code == 302

    # Student attempts to access placement dashboard -> 403 Access Denied
    resp = client.get('/placement/dashboard')
    assert resp.status_code == 403 or b"Access Denied" in resp.data or resp.status_code == 302
    client.get('/logout')

    # Faculty attempts to access admin portal -> 403 Access Denied
    login_client(client, 'test_faculty', 'Faculty@123')
    resp = client.get('/admin/dashboard')
    assert resp.status_code == 403 or b"Access Denied" in resp.data or resp.status_code == 302
    client.get('/logout')


def test_admin_portal_operations(client, app):
    """Verify admin portal can manage students, faculty, and export reports."""
    login_client(client, 'test_admin', 'Admin@123')

    # Enroll student
    resp = client.post('/admin/students', data={
        'student_id': 'STU_NEW_999',
        'first_name': 'Kavya',
        'last_name': 'Nair',
        'email': 'kavya.nair@test.com',
        'department': 'Computer Science & Engineering',
        'academic_year': '1',
        'semester': '1',
        'section': 'A'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Kavya" in resp.data

    with app.app_context():
        new_stu = Student.query.filter_by(student_id='STU_NEW_999').first()
        assert new_stu is not None
        assert new_stu.first_name == 'Kavya'

    # Export reports
    resp = client.get('/admin/reports/export/students')
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert b"STU_NEW_999" in resp.data

    # View Academic Analytics
    resp_analytics = client.get('/admin/analytics')
    assert resp_analytics.status_code == 200
    assert b"Institutional Academic Analytics" in resp_analytics.data
    assert b"Institutional Mean GPA" in resp_analytics.data

    client.get('/logout')


def test_admin_academic_analytics_view(client):
    """Verify /admin/analytics renders real academic summary metrics without UndefinedError."""
    login_client(client, 'test_admin', 'Admin@123')
    resp = client.get('/admin/analytics')
    assert resp.status_code == 200
    assert b"Institutional Mean GPA" in resp.data
    assert b"Passing Rate" in resp.data
    assert b"Standing Backlogs" in resp.data
    assert b"Dean's Honor Roll" in resp.data
    assert b"Department Academic Comparison" in resp.data
    client.get('/logout')


def test_faculty_portal_operations(client, app):
    """Verify faculty can mark attendance, record subject marks, and create mentoring notes."""
    login_client(client, 'test_faculty', 'Faculty@123')

    # Mark attendance
    resp = client.post('/faculty/attendance/mark', data={
        'class_code': 'CSE-SEM3-A',
        'semester': '3',
        'subject': 'Data Structures',
        'session_date': str(date.today()),
        'time_slot': '09:00 - 10:00 AM',
        'status_STU_TEST001': 'Present',
        'remarks_STU_TEST001': 'On time'
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        session_obj = AttendanceSession.query.filter_by(class_code='CSE-SEM3-A', subject='Data Structures').first()
        assert session_obj is not None
        rec = AttendanceRecord.query.filter_by(session_id=session_obj.id, student_id='STU_TEST001').first()
        assert rec is not None
        assert rec.status == 'Present'

    # Record Subject Marks
    resp = client.post('/faculty/academics', data={
        'student_id': 'STU_TEST001',
        'semester': '3',
        'subject_name': 'Data Structures',
        'internal_marks': '28.0',
        'external_marks': '62.0'
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        score = SubjectScore.query.filter_by(student_id='STU_TEST001', subject_name='Data Structures').first()
        assert score is not None
        assert score.marks_obtained == 90.0
        assert score.grade == 'O'

    # Create Mentoring Note
    resp = client.post('/faculty/mentoring', data={
        'student_id': 'STU_TEST001',
        'title': 'Mid-Term Academic Guidance',
        'category': 'Academic',
        'priority': 'Medium',
        'notes': 'Met with student regarding project milestones.',
        'action_items': 'Submit code review draft by Friday.'
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        inter = Intervention.query.filter_by(student_id='STU_TEST001', title='Mid-Term Academic Guidance').first()
        assert inter is not None
        assert inter.priority == 'Medium'

    client.get('/logout')


def test_placement_portal_operations(client, app):
    """Verify placement officer can register companies, jobs, update applications, and log offers."""
    login_client(client, 'test_placement', 'Placement@123')

    # Add Company
    resp = client.post('/placement/companies', data={
        'name': 'Oracle Cloud Infrastructure',
        'industry': 'Enterprise Cloud',
        'min_cgpa': '7.0',
        'eligible_departments': 'Computer Science & Engineering',
        'required_skills': 'Java, Python, Cloud',
        'contact_person': 'Ananya Sen',
        'contact_email': 'ananya.s@oracle.com'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Oracle Cloud Infrastructure" in resp.data

    with app.app_context():
        comp = Company.query.filter_by(name='Oracle Cloud Infrastructure').first()
        assert comp is not None

        # Post Job Opportunity
        job = JobOpportunity(
            company_id=comp.id,
            title='Cloud Infrastructure Engineer',
            ctc_package='15.0 LPA',
            min_cgpa=7.0,
            min_readiness=65.0
        )
        db.session.add(job)
        db.session.commit()

        # Create Application
        app_obj = JobApplication(
            student_id='STU_TEST001',
            job_id=job.id,
            stage='Applied'
        )
        db.session.add(app_obj)
        db.session.commit()
        app_id = app_obj.id

    # Update Application Stage to Interview
    resp = client.post(f'/placement/applications/{app_id}/update-stage', data={
        'stage': 'Interview',
        'feedback': 'Cleared coding challenge with high score.'
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        updated_app = JobApplication.query.get(app_id)
        assert updated_app.stage == 'Interview'

    # Log Placement Offer
    resp = client.post('/placement/offers', data={
        'student_id': 'STU_TEST001',
        'company_name': 'Oracle Cloud Infrastructure',
        'job_title': 'Cloud Infrastructure Engineer',
        'ctc_package': '15.0 LPA',
        'status': 'Accepted'
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        offer = PlacementOffer.query.filter_by(student_id='STU_TEST001', company_name='Oracle Cloud Infrastructure').first()
        assert offer is not None
        assert offer.ctc_numeric == 15.0

    client.get('/logout')
