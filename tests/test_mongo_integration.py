import pytest
from backend.db_mongo import MongoManager, mongo_manager
from backend.models.mongo_models import (
    MongoStudentSchema, MongoAcademicSchema, MongoAttendanceSchema,
    MongoSkillsLearningSchema, MongoFeedbackSchema, MongoRecommendationSchema
)
from backend.services.mongo_service import MongoStudentService
from backend.models.user import User
from backend.models.student import Student

def test_mongo_schema_validations():
    """Verify document schema validation rules across all 6 core domains."""
    # 1. Student Profile Schema
    valid, err = MongoStudentSchema.validate({'student_id': 'STU999', 'first_name': 'Test', 'last_name': 'User', 'email': 'test@campus.edu', 'department': 'CSE'})
    assert valid is True
    assert err is None

    invalid, err = MongoStudentSchema.validate({'student_id': '', 'first_name': 'Test'})
    assert invalid is False
    assert "student_id is required" in err

    # 2. Academic Schema
    valid_ac, err_ac = MongoAcademicSchema.validate({'student_id': 'STU999', 'semester': 3})
    assert valid_ac is True
    assert err_ac is None

    # 3. Attendance Schema
    valid_att, err_att = MongoAttendanceSchema.validate({'student_id': 'STU999', 'status': 'Present'})
    assert valid_att is True
    invalid_att, err_att = MongoAttendanceSchema.validate({'student_id': 'STU999', 'status': 'InvalidStatus'})
    assert invalid_att is False

    # 4. Skills & Learning Schema
    valid_sk, _ = MongoSkillsLearningSchema.validate({'student_id': 'STU999'})
    assert valid_sk is True

    # 5. Feedback Schema
    valid_fb, _ = MongoFeedbackSchema.validate({'student_id': 'STU999'})
    assert valid_fb is True

    # 6. Recommendation Schema
    valid_rec, _ = MongoRecommendationSchema.validate({'student_id': 'STU999', 'title': 'Mentoring Session', 'suggested_action': 'Attend office hours'})
    assert valid_rec is True


def test_mongo_manager_status_and_resilience():
    """Verify MongoManager handles offline/configured state gracefully."""
    mgr = MongoManager()
    status = mgr.get_status()
    assert isinstance(status, dict)
    assert 'connected' in status
    assert 'database' in status
    assert 'timestamp' in status


def test_mongo_api_status_endpoint(client):
    """Verify /api/v1/mongo/status returns diagnostic metadata."""
    res = client.get('/api/v1/mongo/status')
    assert res.status_code in [200, 503]
    data = res.get_json()
    assert 'atlas' in data
    assert 'status' in data


def test_mongo_api_auth_protection(client):
    """Verify student endpoints enforce authentication and role isolation."""
    # Unauthenticated request should redirect or fail
    res = client.get('/api/v1/mongo/students')
    assert res.status_code in [302, 401]

    # Login as Student STU_TEST001
    with client.session_transaction() as sess:
        sess['user_id'] = 4
        sess['role'] = 'Student'
        sess['username'] = 'test_student'
        sess['student_id'] = 'STU_TEST001'

    # Student accessing their own record is permitted
    res_own = client.get('/api/v1/mongo/students/STU_TEST001')
    # Can be 200 or 404 depending on Mongo connection, but MUST NOT be 403 Forbidden
    assert res_own.status_code in [200, 404]

    # Student attempting to access another student's record MUST be 403 Forbidden
    res_other = client.get('/api/v1/mongo/students/STU_DIFFERENT999')
    assert res_other.status_code == 403
    assert "Unauthorized" in res_other.get_json().get('error', '')


def test_mongo_admin_student_crud_routes(client):
    """Verify Admin role has permission to create, update, and delete in MongoDB API."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'Admin'
        sess['username'] = 'test_admin'

    # 1. List students
    res_list = client.get('/api/v1/mongo/students')
    assert res_list.status_code == 200

    # 2. Student validation on create
    res_create_invalid = client.post('/api/v1/mongo/students', json={'student_id': ''})
    assert res_create_invalid.status_code == 400
