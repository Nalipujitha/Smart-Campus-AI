import os
import pytest
from datetime import date
from backend.app import create_app
from backend.config import TestConfig
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.placement import PlacementProfile
from backend.models.audit import SystemConfig, StudentScore

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test admin & faculty & student
        admin = User(username='test_admin', email='admin@test.com', full_name='Test Admin', role='Admin')
        admin.set_password('Admin@123')
        db.session.add(admin)

        faculty = User(username='test_faculty', email='faculty@test.com', full_name='Test Faculty', role='Faculty', department='Computer Science & Engineering')
        faculty.set_password('Faculty@123')
        db.session.add(faculty)

        placement = User(username='test_placement', email='placement@test.com', full_name='Test Placement Officer', role='Placement_Officer')
        placement.set_password('Placement@123')
        db.session.add(placement)

        student_user = User(username='test_student', email='stu@test.com', full_name='Test Student', role='Student', student_id='STU_TEST001')
        student_user.set_password('Student@123')
        db.session.add(student_user)

        # Seed sample student profile
        stu = Student(
            student_id='STU_TEST001',
            first_name='Rahul',
            last_name='Sharma',
            email='stu@test.com',
            department='Computer Science & Engineering',
            academic_year=2,
            semester=3,
            section='A'
        )
        db.session.add(stu)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def login_client(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
