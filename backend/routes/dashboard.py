from datetime import datetime, date
from collections import defaultdict
from flask import Blueprint, render_template, request, session, redirect, url_for
from backend.routes.auth import login_required, get_current_user
from backend.services.institutional_analytics import InstitutionalAnalyticsService
from backend.services.success_score import SuccessScoreService
from backend.services.attendance_service import AttendanceService
from backend.services.segmentation import StudentSegmentationService
from backend.services.recommendations import RecommendationService
from backend.models.student import Student
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.placement import PlacementProfile, PracticeAttempt
from backend.models.learning import LearningPlan, LearningTask, LmsActivity
from backend.models.recommendation import Recommendation
from backend.models.user import User

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    if user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'Faculty':
        return redirect(url_for('faculty.dashboard'))
    elif user.role in ['Placement_Officer', 'Placement']:
        return redirect(url_for('placement.dashboard'))
    else:
        return redirect(url_for('dashboard.student_dashboard'))


@dashboard_bp.route('/student/dashboard')
@dashboard_bp.route('/dashboard/student')
@login_required
def student_dashboard():
    user = get_current_user()

    student = None
    if user.student_id:
        student = Student.query.filter_by(student_id=user.student_id).first()
    
    # Fallback if student account is not linked to student_id yet
    if not student:
        student = Student.query.first()

    student_data = {}
    if student:
        # 1. Success Score Details
        score_data = SuccessScoreService.calculate_student_score(student, save_db=False)
        
        # 2. Attendance Details
        att_data = AttendanceService.calculate_student_attendance(student.student_id)
        
        # Attendance by Subject
        att_records = AttendanceRecord.query.filter_by(student_id=student.student_id).join(AttendanceSession).filter(AttendanceSession.is_cancelled == False).all()
        
        subj_att = defaultdict(lambda: {'total': 0, 'present': 0, 'absent': 0, 'leave': 0})
        monthly_att = defaultdict(lambda: {'total': 0, 'present': 0})
        
        for r in att_records:
            s_name = r.session.subject
            s_date = r.session.session_date
            m_key = s_date.strftime('%b %Y') if isinstance(s_date, (datetime, date)) else 'Recent'
            
            subj_att[s_name]['total'] += 1
            monthly_att[m_key]['total'] += 1
            if r.status == 'Present':
                subj_att[s_name]['present'] += 1
            elif r.status == 'Absent':
                subj_att[s_name]['absent'] += 1
            elif r.status == 'On Leave':
                subj_att[s_name]['leave'] += 1

        subject_attendance_list = []
        for s_name, stats in subj_att.items():
            pct = round((stats['present'] / stats['total'] * 100), 1) if stats['total'] > 0 else 0.0
            subject_attendance_list.append({
                'subject': s_name,
                'total': stats['total'],
                'present': stats['present'],
                'absent': stats['absent'],
                'leave': stats['leave'],
                'percentage': pct
            })

        monthly_trend_list = []
        for m_key, m_stats in sorted(monthly_att.items()):
            pct = round((m_stats['present'] / m_stats['total'] * 100), 1) if m_stats['total'] > 0 else 0.0
            monthly_trend_list.append({
                'month': m_key,
                'total': m_stats['total'],
                'present': m_stats['present'],
                'percentage': pct
            })

        # 3. Academic Details
        academic_record = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.desc()).first()
        subject_scores = SubjectScore.query.filter_by(student_id=student.student_id, semester=student.semester).all()
        
        # If no subject scores for current semester, fetch previous semester scores
        if not subject_scores:
            subject_scores = SubjectScore.query.filter_by(student_id=student.student_id).order_by(SubjectScore.semester.desc()).limit(6).all()

        strong_subjects = [s for s in subject_scores if (s.marks_obtained / s.max_marks * 100) >= 75.0] if subject_scores else []
        weak_subjects = [s for s in subject_scores if (s.marks_obtained / s.max_marks * 100) < 75.0] if subject_scores else []

        # 4. Placement Profile
        placement_profile = PlacementProfile.query.filter_by(student_id=student.student_id).first()
        practice_attempts_count = PracticeAttempt.query.filter_by(student_id=student.student_id).count()

        # 5. Learning Plans & LMS
        learning_plans = LearningPlan.query.filter_by(student_id=student.student_id).all()
        total_tasks = 0
        completed_tasks = 0
        pending_tasks_list = []
        for lp in learning_plans:
            for task in lp.tasks:
                total_tasks += 1
                if task.is_completed:
                    completed_tasks += 1
                else:
                    pending_tasks_list.append(task)
        
        lms_activities = LmsActivity.query.filter_by(student_id=student.student_id).all()
        lms_avg_completion = round(sum(a.completion_percentage for a in lms_activities) / len(lms_activities), 1) if lms_activities else 0.0

        # 6. Recommendations & Segmentation
        recommendations = Recommendation.query.filter_by(student_id=student.student_id).order_by(Recommendation.created_at.desc()).all()
        if not recommendations:
            RecommendationService.generate_student_recommendations(student, save_db=True)
            recommendations = Recommendation.query.filter_by(student_id=student.student_id).order_by(Recommendation.created_at.desc()).all()

        # Compute matched segments
        from backend.models.audit import StudentScore
        score_rec = StudentScore.query.filter_by(student_id=student.student_id).first()
        matched_segments = StudentSegmentationService.evaluate_student_segments(
            score_rec or type('ScoreObj', (), score_data),
            student
        )
        score_data['matched_segments'] = matched_segments

        # 7. Assigned Faculty Mentor
        mentor = User.query.get(student.mentor_id) if student.mentor_id else None

        # 8. Dynamic Notifications & Low-Attendance / Academic Alerts
        notifications = []
        if att_data['percentage'] < 75.0 and att_data['total_sessions'] > 0:
            notifications.append({
                'type': 'warning',
                'title': 'Low Attendance Notice',
                'message': f"Your attendance is currently {att_data['percentage']}%, which is below the mandatory 75% threshold.",
                'time': 'Action required'
            })
        if weak_subjects:
            notifications.append({
                'type': 'info',
                'title': 'Academic Focus Area',
                'message': f"Recommended practice available for {weak_subjects[0].subject_name}.",
                'time': 'Recent'
            })
        if placement_profile and placement_profile.readiness_percentage < 60.0:
            notifications.append({
                'type': 'primary',
                'title': 'Placement Preparation',
                'message': 'Complete your aptitude and coding practice sets to boost placement readiness.',
                'time': 'Skill drill'
            })

        is_feedback_eligible = (att_data['percentage'] >= 75.0) and (lms_avg_completion >= 75.0)

        student_data = {
            'student': student,
            'score_data': score_data,
            'att_data': att_data,
            'subject_attendance_list': subject_attendance_list,
            'monthly_trend_list': monthly_trend_list,
            'academic_record': academic_record,
            'subject_scores': subject_scores,
            'strong_subjects': strong_subjects,
            'weak_subjects': weak_subjects,
            'placement_profile': placement_profile,
            'practice_attempts_count': practice_attempts_count,
            'learning_plans': learning_plans,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks_list': pending_tasks_list,
            'lms_activities': lms_activities,
            'lms_avg_completion': lms_avg_completion,
            'recommendations': recommendations,
            'mentor': mentor,
            'notifications': notifications,
            'is_feedback_eligible': is_feedback_eligible
        }

    return render_template(
        'index.html',
        user=user,
        student=student,
        student_data=student_data,
        is_student_view=True,
        last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
