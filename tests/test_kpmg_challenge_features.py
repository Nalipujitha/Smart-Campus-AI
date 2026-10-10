import pytest
from datetime import date
from backend.extensions import db
from backend.models.student import Student
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.placement import PlacementProfile
from backend.models.learning import LmsActivity
from backend.models.audit import StudentScore, EngagementRecord, FeedbackRecord
from backend.models.recommendation import Recommendation
from backend.models.intervention import Intervention
from backend.services.success_score import SuccessScoreService
from backend.services.risk_analysis import RiskAnalysisService
from backend.services.segmentation import StudentSegmentationService
from backend.services.recommendations import RecommendationService
from backend.services.institutional_analytics import InstitutionalAnalyticsService
from tests.conftest import login_client

def test_feature1_at_risk_student_identification(app):
    """Test Feature 1: Multi-factor risk identification and immediate attention flags."""
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_TEST001').first()
        
        # Test High Risk student with critical attendance and academic struggles
        eval_res = RiskAnalysisService.evaluate_risk(
            student_id=stu.student_id,
            success_score=42.5,
            academic_score=45.0,
            attendance_score=58.0,
            lms_score=40.0,
            placement_score=35.0,
            academic_year=3
        )

        assert eval_res['risk_level'] == 'High'
        assert eval_res['academic_risk'] == 'High'
        assert eval_res['placement_risk'] == 'High'
        assert eval_res['needs_immediate_attention'] is True
        assert len(eval_res['risk_factors']) >= 3
        assert eval_res['critical_factor_count'] >= 2

        # Verify trigger evidence format
        dims = [f['dimension'] for f in eval_res['risk_factors']]
        assert 'Attendance' in dims
        assert 'Academic Standing' in dims
        assert 'Placement Readiness' in dims

def test_feature2_explainable_success_score(app):
    """Test Feature 2: Explainable 7-indicator score calculation (0-100), status labels, and contributors."""
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_TEST001').first()

        # Seed academic, attendance, LMS, placement data
        acad = AcademicRecord(student_id=stu.student_id, semester=3, gpa=8.2, backlogs_count=0)
        db.session.add(acad)

        session_rec = AttendanceSession(department=stu.department, class_code='CSE-SEM3', semester=3, subject='Data Structures', session_date=date.today())
        db.session.add(session_rec)
        db.session.flush()

        att_rec = AttendanceRecord(session_id=session_rec.id, student_id=stu.student_id, status='Present')
        db.session.add(att_rec)

        lms = LmsActivity(student_id=stu.student_id, course_name='CS201', modules_completed=8, total_modules=10, quiz_score_avg=80.0)
        db.session.add(lms)

        placement = PlacementProfile(
            student_id=stu.student_id,
            target_role='Full Stack Developer',
            coding_score=78.0,
            aptitude_score=72.0,
            communication_score=75.0,
            interview_score=74.0,
            readiness_percentage=75.0
        )
        db.session.add(placement)
        db.session.commit()

        score_res = SuccessScoreService.calculate_student_score(stu, save_db=True)

        assert 0.0 <= score_res['score'] <= 100.0
        assert score_res['score'] == score_res['success_score']
        assert score_res['status_label'] in ['High Performing', 'Good Standing', 'Moderate Risk', 'Critical Risk']
        assert 'status_color' in score_res
        assert len(score_res['indicators']) == 7
        
        # Verify positive contributors and improvement areas separation
        assert isinstance(score_res['positive_contributors'], list)
        assert isinstance(score_res['improvement_areas'], list)
        assert len(score_res['positive_contributors']) + len(score_res['improvement_areas']) == 7

        # Verify weights sum to 100%
        weight_sum = sum(score_res['weights_applied'].values())
        assert abs(weight_sum - 1.0) < 0.001

def test_feature3_student_segmentation(app):
    """Test Feature 3: Rule-based student segmentation for the 5 required cohorts."""
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_TEST001').first()

        # 1. High Academic / Low Placement Gap student
        mock_score_1 = StudentScore(
            student_id=stu.student_id,
            academic_component=88.0,
            attendance_component=85.0,
            lms_component=80.0,
            placement_component=42.0,
            success_score=74.0,
            risk_level='Low'
        )
        matched_1 = StudentSegmentationService.evaluate_student_segments(mock_score_1, stu)
        seg_ids_1 = [m['segment_id'] for m in matched_1]
        assert 'academic_achievers_placement_gap' in seg_ids_1

        # 2. Attendance & Academic At-Risk student
        mock_score_2 = StudentScore(
            student_id=stu.student_id,
            academic_component=48.0,
            attendance_component=62.0,
            lms_component=50.0,
            placement_component=40.0,
            success_score=49.0,
            risk_level='High'
        )
        matched_2 = StudentSegmentationService.evaluate_student_segments(mock_score_2, stu)
        seg_ids_2 = [m['segment_id'] for m in matched_2]
        assert 'attendance_academic_at_risk' in seg_ids_2
        assert 'core_support_group' in seg_ids_2

        # 3. All-Round Placement Ready student
        mock_score_3 = StudentScore(
            student_id=stu.student_id,
            academic_component=85.0,
            attendance_component=90.0,
            lms_component=85.0,
            placement_component=82.0,
            success_score=85.0,
            risk_level='Low'
        )
        matched_3 = StudentSegmentationService.evaluate_student_segments(mock_score_3, stu)
        seg_ids_3 = [m['segment_id'] for m in matched_3]
        assert 'all_round_placement_ready' in seg_ids_3

        # 4. Disengaged High-Potential (LMS Gap)
        mock_score_4 = StudentScore(
            student_id=stu.student_id,
            academic_component=82.0,
            attendance_component=80.0,
            lms_component=40.0,
            placement_component=65.0,
            success_score=72.0,
            risk_level='Low'
        )
        matched_4 = StudentSegmentationService.evaluate_student_segments(mock_score_4, stu)
        seg_ids_4 = [m['segment_id'] for m in matched_4]
        assert 'disengaged_high_potential' in seg_ids_4

        # Verify aggregate segmentation output
        all_segs = StudentSegmentationService.get_all_segments()
        assert len(all_segs['segments']) == 5

def test_feature4_actionable_recommendations_and_status(app):
    """Test Feature 4: Recommendation generation, roles, deadlines, and persistence."""
    with app.app_context():
        stu = Student.query.filter_by(student_id='STU_TEST001').first()

        # Seed low attendance and low coding scores
        session_rec = AttendanceSession(department=stu.department, class_code='CSE-SEM3', semester=3, subject='CS101', session_date=date.today())
        db.session.add(session_rec)
        db.session.flush()

        att_rec = AttendanceRecord(session_id=session_rec.id, student_id=stu.student_id, status='Absent')
        db.session.add(att_rec)

        placement = PlacementProfile(
            student_id=stu.student_id,
            target_role='Software Engineer',
            coding_score=45.0,
            aptitude_score=50.0,
            communication_score=55.0,
            interview_score=50.0,
            readiness_percentage=48.0
        )
        db.session.add(placement)
        db.session.commit()

        recs = RecommendationService.generate_student_recommendations(stu, save_db=True)
        assert len(recs) >= 2

        # Verify attributes
        for r in recs:
            assert 'title' in r
            assert 'priority' in r
            assert 'responsible_role' in r
            assert 'suggested_deadline' in r
            assert 'suggested_action' in r

        # Test status update persistence
        rec_obj = Recommendation.query.filter_by(student_id=stu.student_id).first()
        assert rec_obj is not None
        
        updated = RecommendationService.update_recommendation_status(rec_obj.id, 'In Progress')
        assert updated.status == 'In Progress'

        # Verify from database
        db_rec = Recommendation.query.get(rec_obj.id)
        assert db_rec.status == 'In Progress'

def test_feature5_admin_decision_intelligence(app):
    """Test Feature 5: Institutional KPI aggregation, distributions, and department comparisons."""
    with app.app_context():
        summary = InstitutionalAnalyticsService.get_dashboard_summary()
        assert 'total_students' in summary
        assert 'avg_success_score' in summary
        assert 'risk_distribution' in summary
        assert 'immediate_attention_count' in summary
        assert 'department_success_scores' in summary
        assert 'segment_distribution' in summary
        assert 'top_risk_factors' in summary
        assert 'intervention_status_distribution' in summary

def test_kpmg_api_endpoints(client, app):
    """Test all new KPMG Challenge API endpoints."""
    with app.app_context():
        # 1. At-Risk students API
        res = client.get('/api/v1/analytics/at-risk-students')
        assert res.status_code == 200
        json_data = res.get_json()
        assert 'students' in json_data
        assert 'count' in json_data

        # 2. Segmentation API
        res_seg = client.get('/api/v1/analytics/segments')
        assert res_seg.status_code == 200
        json_seg = res_seg.get_json()
        assert len(json_seg['segments']) == 5

        # 3. Individual Segment API
        res_single_seg = client.get('/api/v1/analytics/segments/academic_achievers_placement_gap')
        assert res_single_seg.status_code == 200
        assert res_single_seg.get_json()['segment_id'] == 'academic_achievers_placement_gap'

        # Invalid segment ID test
        res_invalid_seg = client.get('/api/v1/analytics/segments/non_existent_segment')
        assert res_invalid_seg.status_code == 404

        # 4. Student Score Breakdown API
        res_score = client.get('/api/v1/students/STU_TEST001/score-breakdown')
        assert res_score.status_code == 200
        score_json = res_score.get_json()
        assert 'score' in score_json
        assert 'indicators' in score_json
        assert 'positive_contributors' in score_json
        assert 'improvement_areas' in score_json

        # Invalid student ID test
        res_invalid_stu = client.get('/api/v1/students/INVALID_ID_999/score-breakdown')
        assert res_invalid_stu.status_code == 404

        # 5. Log Intervention Follow-Up API
        interv_payload = {
            'student_id': 'STU_TEST001',
            'title': 'Faculty Academic Mentoring Review',
            'category': 'Academic',
            'priority': 'High',
            'status': 'In Progress',
            'notes': 'Discussed study schedules and subject doubts in Data Structures.'
        }
        res_inv = client.post('/api/v1/interventions/record', json=interv_payload)
        assert res_inv.status_code == 201
        inv_data = res_inv.get_json()['intervention']
        assert inv_data['student_id'] == 'STU_TEST001'
        assert inv_data['status'] == 'In Progress'
