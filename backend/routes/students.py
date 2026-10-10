from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from backend.extensions import db
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.student import Student
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceRecord, AttendanceSession
from backend.models.learning import LmsActivity, LearningPlan
from backend.models.placement import PlacementProfile
from backend.models.intervention import Intervention
from backend.models.recommendation import Recommendation
from backend.models.audit import AuditEvent, StudentScore, EngagementRecord, FeedbackRecord
from backend.services.success_score import SuccessScoreService
from backend.services.attendance_service import AttendanceService
from backend.services.risk_analysis import RiskAnalysisService
from backend.db_mongo import mongo_manager
from backend.services.mongo_service import MongoStudentService

students_bp = Blueprint('students', __name__)

@students_bp.route('/')
@login_required
def list_students():
    user = get_current_user()
    if user.role == 'Student':
        # Student role can only see their own profile
        return redirect(url_for('students.view_student', student_id=user.student_id))

    # Filters
    department = request.args.get('department')
    year = request.args.get('academic_year', type=int)
    semester = request.args.get('semester', type=int)
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)

    query = Student.query

    # Faculty can view all or filter by department
    if department:
        query = query.filter(Student.department == department)
    if year:
        query = query.filter(Student.academic_year == year)
    if semester:
        query = query.filter(Student.semester == semester)
    if status:
        query = query.filter(Student.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Student.student_id.ilike(search_pattern)) |
            (Student.first_name.ilike(search_pattern)) |
            (Student.last_name.ilike(search_pattern)) |
            (Student.email.ilike(search_pattern))
        )

    pagination = query.order_by(Student.student_id.asc()).paginate(page=page, per_page=per_page, error_out=False)
    students = pagination.items

    # Fetch scores for fast display
    student_ids = [s.student_id for s in students]
    scores = {sc.student_id: sc for sc in StudentScore.query.filter(StudentScore.student_id.in_(student_ids)).all()}

    departments = [
        'Computer Science & Engineering',
        'Electronics & Communication',
        'Information Technology',
        'Artificial Intelligence & Data Science',
        'Mechanical Engineering'
    ]

    return render_template(
        'students.html',
        user=user,
        students=students,
        scores=scores,
        pagination=pagination,
        departments=departments,
        selected_dept=department,
        selected_year=year,
        selected_sem=semester,
        selected_status=status,
        search=search
    )

@students_bp.route('/<student_id>')
@login_required
def view_student(student_id):
    user = get_current_user()
    
    # Permission Enforcement: Student can only view their own profile
    if user.role == 'Student' and user.student_id != student_id:
        flash("Unauthorized: You are only permitted to view your own student profile.", "danger")
        return redirect(url_for('students.view_student', student_id=user.student_id))

    student = Student.query.filter_by(student_id=student_id).first_or_404()
    
    # Calculate or fetch latest success score & breakdown
    score_data = SuccessScoreService.calculate_student_score(student, save_db=True)
    att_stats = AttendanceService.calculate_student_attendance(student.student_id)
    
    academic_recs = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.asc()).all()
    subject_scores = SubjectScore.query.filter_by(student_id=student.student_id).all()
    lms_activities = LmsActivity.query.filter_by(student_id=student.student_id).all()
    interventions = Intervention.query.filter_by(student_id=student.student_id).order_by(Intervention.session_date.desc()).all()
    recommendations = Recommendation.query.filter_by(student_id=student.student_id, status='Active').all()
    placement = PlacementProfile.query.filter_by(student_id=student.student_id).first()
    engagements = EngagementRecord.query.filter_by(student_id=student.student_id).all()
    feedbacks = FeedbackRecord.query.filter_by(student_id=student.student_id).all()
    learning_plans = LearningPlan.query.filter_by(student_id=student.student_id).all()

    # Calculate feedback eligibility: Attendance >= 75% AND Course/LMS Activity >= 75%
    att_pct = att_stats.get('attendance_percentage') or 0.0
    avg_lms_pct = 0.0
    if lms_activities:
        avg_lms_pct = sum(a.completion_percentage for a in lms_activities) / len(lms_activities)

    is_feedback_eligible = (att_pct >= 75.0 and avg_lms_pct >= 75.0)
    feedback_eligibility = {
        'is_eligible': is_feedback_eligible,
        'attendance_pct': att_pct,
        'lms_activeness_pct': round(avg_lms_pct, 1),
        'threshold': 75.0,
        'reason': "✅ Eligible to submit institutional feedback." if is_feedback_eligible else f"🔒 Feedback Locked: Minimum 75% attendance (Current: {att_pct}%) and 75% course LMS completion (Current: {round(avg_lms_pct, 1)}%) required."
    }

    # Sync to MongoDB Atlas in background / inline if connected
    try:
        if MongoStudentService.is_connected():
            MongoStudentService.sync_student_to_mongo(student)
    except Exception:
        pass

    mongo_status = mongo_manager.get_status()

    return render_template(
        'student_profile.html',
        user=user,
        student=student,
        score=score_data,
        attendance=att_stats,
        academic_records=academic_recs,
        subject_scores=subject_scores,
        lms_activities=lms_activities,
        interventions=interventions,
        recommendations=recommendations,
        placement=placement,
        engagements=engagements,
        feedbacks=feedbacks,
        learning_plans=learning_plans,
        feedback_eligibility=feedback_eligibility,
        mongo_status=mongo_status
    )

@students_bp.route('/<student_id>/submit-feedback', methods=['POST'])
@login_required
def submit_feedback(student_id):
    student = Student.query.filter_by(student_id=student_id).first_or_404()
    user = get_current_user()

    # Verify eligibility (Attendance >= 75% AND LMS completion >= 75%)
    att_stats = AttendanceService.calculate_student_attendance(student.student_id)
    att_pct = att_stats.get('attendance_percentage') or 0.0
    lms_activities = LmsActivity.query.filter_by(student_id=student.student_id).all()
    avg_lms_pct = sum(a.completion_percentage for a in lms_activities) / len(lms_activities) if lms_activities else 0.0

    if att_pct < 75.0 or avg_lms_pct < 75.0:
        flash(f"Ineligible: Feedback submission requires minimum 75% attendance (Current: {att_pct}%) and 75% course LMS completion (Current: {round(avg_lms_pct, 1)}%).", "danger")
        return redirect(url_for('students.view_student', student_id=student_id))

    b_score = float(request.form.get('behavioral_score', 85.0))
    p_score = float(request.form.get('punctuality_score', 85.0))
    t_score = float(request.form.get('teamwork_score', 85.0))
    i_score = float(request.form.get('initiative_score', 85.0))
    notes = request.form.get('general_notes', '').strip()
    term = request.form.get('term', 'Semester Feedback')

    feedback = FeedbackRecord(
        student_id=student_id,
        faculty_id=user.id if user.role == 'Faculty' else None,
        behavioral_score=b_score,
        punctuality_score=p_score,
        teamwork_score=t_score,
        initiative_score=i_score,
        general_notes=notes,
        term=term
    )
    db.session.add(feedback)
    db.session.commit()

    # Recalculate student composite score
    SuccessScoreService.calculate_student_score(student, save_db=True)
    try:
        if MongoStudentService.is_connected():
            MongoStudentService.sync_student_to_mongo(student)
    except Exception:
        pass

    flash("Feedback successfully submitted! Student support score updated.", "success")
    return redirect(url_for('students.view_student', student_id=student_id))

@students_bp.route('/create', methods=['POST'])
@login_required
@roles_required('Admin')
def create_student():
    data = request.form
    student_id = data.get('student_id', '').strip().upper()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip().lower()
    department = data.get('department')
    year = int(data.get('academic_year', 1))
    semester = int(data.get('semester', 1))
    section = data.get('section', 'A')

    if not student_id or not first_name or not last_name or not email or not department:
        flash("All mandatory student fields must be provided.", "danger")
        return redirect(url_for('students.list_students'))

    if Student.query.filter_by(student_id=student_id).first():
        flash(f"Student ID '{student_id}' already exists in database.", "danger")
        return redirect(url_for('students.list_students'))

    new_stu = Student(
        student_id=student_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=department,
        academic_year=year,
        semester=semester,
        section=section
    )
    db.session.add(new_stu)
    db.session.commit()

    # Initialize score & profile
    SuccessScoreService.calculate_student_score(new_stu, save_db=True)
    try:
        if MongoStudentService.is_connected():
            MongoStudentService.sync_student_to_mongo(new_stu)
    except Exception:
        pass
    
    # Audit log
    audit = AuditEvent(
        user_id=session.get('user_id'),
        action="STUDENT_CREATE",
        module="Students",
        details=f"Created student record for {student_id} ({first_name} {last_name})."
    )
    db.session.add(audit)
    db.session.commit()

    flash(f"Student {student_id} created successfully.", "success")
    return redirect(url_for('students.view_student', student_id=student_id))

@students_bp.route('/<student_id>/edit', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def edit_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first_or_404()
    data = request.form

    student.first_name = data.get('first_name', student.first_name).strip()
    student.last_name = data.get('last_name', student.last_name).strip()
    student.department = data.get('department', student.department)
    student.academic_year = int(data.get('academic_year', student.academic_year))
    student.semester = int(data.get('semester', student.semester))
    student.section = data.get('section', student.section)
    student.status = data.get('status', student.status)

    db.session.commit()
    SuccessScoreService.calculate_student_score(student, save_db=True)
    try:
        if MongoStudentService.is_connected():
            MongoStudentService.sync_student_to_mongo(student)
    except Exception:
        pass

    flash(f"Student details updated successfully.", "success")
    return redirect(url_for('students.view_student', student_id=student_id))

@students_bp.route('/<student_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first_or_404()
    stu_id = student.student_id

    audit = AuditEvent(
        user_id=session.get('user_id'),
        action="STUDENT_DELETE",
        module="Students",
        details=f"Deleted student {stu_id} ({student.full_name})."
    )
    db.session.add(audit)
    db.session.delete(student)
    db.session.commit()

    try:
        if MongoStudentService.is_connected():
            MongoStudentService.delete_student(stu_id)
    except Exception:
        pass

    flash(f"Student {stu_id} deleted successfully.", "info")
    return redirect(url_for('students.list_students'))
