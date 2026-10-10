import pytest
from datetime import date
from tests.conftest import login_client
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.services.attendance_service import AttendanceService
from backend.extensions import db

def test_attendance_session_creation(client, app):
    login_client(client, 'test_faculty', 'Faculty@123')
    response = client.post('/attendance/record', data={
        'department': 'Computer Science & Engineering',
        'semester': 3,
        'subject': 'Data Structures',
        'session_date': date.today().isoformat(),
        'status_STU_TEST001': 'Present',
        'remarks_STU_TEST001': 'Attentive'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        sess = AttendanceSession.query.filter_by(subject='Data Structures').first()
        assert sess is not None
        rec = AttendanceRecord.query.filter_by(session_id=sess.id, student_id='STU_TEST001').first()
        assert rec is not None
        assert rec.status == 'Present'

def test_attendance_calculation_present_and_absent(app):
    with app.app_context():
        sess1 = AttendanceSession(department='CSE', class_code='CSE1', semester=1, subject='Math', session_date=date.today())
        sess2 = AttendanceSession(department='CSE', class_code='CSE1', semester=1, subject='Math', session_date=date.today())
        db.session.add_all([sess1, sess2])
        db.session.flush()

        r1 = AttendanceRecord(session_id=sess1.id, student_id='STU_TEST001', status='Present')
        r2 = AttendanceRecord(session_id=sess2.id, student_id='STU_TEST001', status='Absent')
        db.session.add_all([r1, r2])
        db.session.commit()

        stats = AttendanceService.calculate_student_attendance('STU_TEST001')
        assert stats['total_sessions'] == 2
        assert stats['present_count'] == 1
        assert stats['absent_count'] == 1
        assert stats['attendance_percentage'] == 50.0
        assert stats['is_below_warning'] is True

def test_duplicate_attendance_prevention(app):
    with app.app_context():
        sess = AttendanceSession(department='CSE', class_code='CSE1', semester=1, subject='Math', session_date=date.today())
        db.session.add(sess)
        db.session.flush()

        r1 = AttendanceRecord(session_id=sess.id, student_id='STU_TEST001', status='Present')
        db.session.add(r1)
        db.session.commit()

        # Duplicate insert on same session_id & student_id must raise integrity error
        r2 = AttendanceRecord(session_id=sess.id, student_id='STU_TEST001', status='Absent')
        db.session.add(r2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
