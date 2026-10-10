from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from backend.routes.auth import login_required, get_current_user
from backend.services.learning_assistant import LearningAssistantService
from backend.models.learning import LearningPlan, LearningTask, LmsActivity
from backend.models.student import Student

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/')
@login_required
def index():
    user = get_current_user()
    
    # Target student determination
    target_student_id = request.args.get('student_id')
    if user.role == 'Student':
        target_student_id = user.student_id
    elif not target_student_id:
        # Default to first active student for faculty demo
        first_stu = Student.query.filter_by(status='Active').first()
        target_student_id = first_stu.student_id if first_stu else 'STU2024001'

    student = Student.query.filter_by(student_id=target_student_id).first()
    
    plans = LearningPlan.query.filter_by(student_id=target_student_id).order_by(LearningPlan.created_at.desc()).all()
    lms_activities = LmsActivity.query.filter_by(student_id=target_student_id).all()
    weak_subjects = LearningAssistantService.get_subject_gaps(target_student_id)
    catalog = LearningAssistantService.LOCAL_RESOURCE_CATALOG

    all_students = Student.query.filter_by(status='Active').order_by(Student.student_id.asc()).limit(50).all()

    return render_template(
        'learning_assistant.html',
        user=user,
        student=student,
        plans=plans,
        lms_activities=lms_activities,
        weak_subjects=weak_subjects,
        catalog=catalog,
        all_students=all_students,
        selected_student_id=target_student_id
    )

@learning_bp.route('/plan/create', methods=['POST'])
@login_required
def create_plan():
    user = get_current_user()
    student_id = request.form.get('student_id')
    if user.role == 'Student':
        student_id = user.student_id

    skill_topic = request.form.get('skill_topic')
    weekly_hours = float(request.form.get('weekly_hours', 5.0))

    if not skill_topic or not student_id:
        flash("Student and learning topic are required.", "danger")
        return redirect(url_for('learning.index', student_id=student_id))

    plan = LearningAssistantService.create_study_plan(
        student_id=student_id,
        skill_topic=skill_topic,
        weekly_hours=weekly_hours
    )

    if plan:
        flash(f"Personalized study plan for '{skill_topic}' created with assigned milestones.", "success")
    else:
        flash("Failed to create study plan.", "danger")

    return redirect(url_for('learning.index', student_id=student_id))

@learning_bp.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    is_completed = request.form.get('is_completed') in ['1', 'true', 'True', True]
    task, err = LearningAssistantService.toggle_task_completion(task_id, is_completed)
    
    if request.is_json:
        if err:
            return jsonify({'error': err}), 400
        return jsonify({
            'success': True,
            'task': task.to_dict(),
            'plan_progress': task.plan.progress_percentage,
            'plan_status': task.plan.status
        })

    if err:
        flash(err, "danger")
    else:
        status_msg = "completed" if is_completed else "marked incomplete"
        flash(f"Task '{task.title}' {status_msg}.", "success")

    return redirect(request.referrer or url_for('learning.index'))
