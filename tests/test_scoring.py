from backend.models.student import Student
from backend.services.success_score import SuccessScoreService

def test_weights_validation():
    valid_weights = {
        'academic': 0.30,
        'attendance': 0.20,
        'lms': 0.10,
        'engagement': 0.10,
        'placement': 0.15,
        'skills': 0.10,
        'feedback': 0.05
    }
    assert SuccessScoreService.validate_weights(valid_weights) is True

    invalid_weights = {
        'academic': 0.50,
        'attendance': 0.20,
        'lms': 0.10,
        'engagement': 0.10,
        'placement': 0.15,
        'skills': 0.10,
        'feedback': 0.05
    }
    assert SuccessScoreService.validate_weights(invalid_weights) is False

def test_score_calculation_boundary_conditions(app):
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_TEST001').first()
        res = SuccessScoreService.calculate_student_score(stu, save_db=True)
        assert res['success_score'] >= 0.0
        assert res['success_score'] <= 100.0
        assert 'academic_component' in res
        assert 'attendance_component' in res
        assert 'risk_level' in res
