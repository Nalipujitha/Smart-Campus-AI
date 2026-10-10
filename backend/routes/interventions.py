from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from backend.extensions import db
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.intervention import Intervention
from backend.models.student import Student
from backend.models.audit import AuditEvent

interventions_bp = Blueprint('interventions', __name__)

@interventions_bp.route('/')
@login_required
def index():
    user = get_current_user()
    if user.role == 'Student':
        # Students see interventions concerning them
        interventions = Intervention.query.filter_by(student_id=user.student_id).order_by(Intervention.session_date.desc()).all()
    elif user.role == 'Faculty':
        # Faculty can see interventions they conducted or departmental
        interventions = Intervention.query.filter(
            (Intervention.faculty_id == user.id) | (Intervention.faculty_id.is_(None))
        ).order_by(Intervention.session_date.desc()).all()
    else:
        # Admin / Placement Officer
        interventions = Intervention.query.order_by(Intervention.session_date.desc()).all()

    # Metrics
    total = len(interventions)
    open_count = sum(1 for i in interventions if i.status == 'Open')
    in_progress_count = sum(1 for i in interventions if i.status == 'In Progress')
    completed_count = sum(1 for i in interventions if i.status == 'Completed')
    overdue_count = sum(1 for i in interventions if i.is_overdue)

    students = Student.query.filter_by(status='Active').order_by(Student.student_id.asc()).all()

    return render_template(
        'interventions.html',
        user=user,
        interventions=interventions,
        students=students,
        total_count=total,
        open_count=open_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        overdue_count=overdue_count,
        today=date.today().isoformat()
    )

@interventions_bp.route('/create', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def create_intervention():
    user = get_current_user()
    student_id = request.form.get('student_id', '').strip()
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Academic')
    priority = request.form.get('priority', 'Medium')
    session_date_str = request.form.get('session_date')
    follow_up_date_str = request.form.get('follow_up_date')
    notes = request.form.get('notes', '').strip()
    action_items = request.form.get('action_items', '').strip()

    if not student_id or not title or not notes:
        flash("Student ID, title, and session notes are mandatory.", "danger")
        return redirect(url_for('interventions.index'))

    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        flash(f"Student with ID '{student_id}' not found.", "danger")
        return redirect(url_for('interventions.index'))

    session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date() if session_date_str else date.today()
    follow_up_date = datetime.strptime(follow_up_date_str, '%Y-%m-%d').date() if follow_up_date_str else None

    intervention = Intervention(
        student_id=student_id,
        faculty_id=user.id,
        title=title,
        category=category,
        priority=priority,
        status='Open',
        session_date=session_date,
        follow_up_date=follow_up_date,
        notes=notes,
        action_items=action_items
    )
    db.session.add(intervention)
    db.session.commit()

    # Audit log
    audit = AuditEvent(
        user_id=user.id,
        action="INTERVENTION_CREATE",
        module="Interventions",
        details=f"Created intervention for student {student_id} ({title})."
    )
    db.session.add(audit)
    db.session.commit()

    flash(f"Intervention session logged for {student.full_name}.", "success")
    return redirect(url_for('interventions.index'))

@interventions_bp.route('/<int:intervention_id>/update', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def update_intervention(intervention_id):
    intervention = Intervention.query.get_or_404(intervention_id)
    user = get_current_user()

    status = request.form.get('status', intervention.status)
    priority = request.form.get('priority', intervention.priority)
    follow_up_date_str = request.form.get('follow_up_date')
    outcome_notes = request.form.get('outcome_notes', '').strip()
    action_items = request.form.get('action_items', '').strip()

    intervention.status = status
    intervention.priority = priority
    if follow_up_date_str:
        intervention.follow_up_date = datetime.strptime(follow_up_date_str, '%Y-%m-%d').date()
    if outcome_notes:
        intervention.outcome_notes = outcome_notes
    if action_items:
        intervention.action_items = action_items

    intervention.updated_at = datetime.utcnow()
    db.session.commit()

    flash(f"Intervention #{intervention_id} updated successfully.", "success")
    return redirect(url_for('interventions.index'))
