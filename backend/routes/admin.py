import io
import csv
import json
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.user import User
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.intervention import Intervention
from backend.models.placement import PlacementProfile, Company, JobOpportunity, JobApplication, PlacementOffer
from backend.models.audit import AuditEvent, SystemConfig
from backend.services.institutional_analytics import InstitutionalAnalyticsService
from backend.services.success_score import SuccessScoreService
from backend.services.attendance_service import AttendanceService
from backend.services.risk_analysis import RiskAnalysisService
from backend.extensions import db

admin_bp = Blueprint('admin', __name__)

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Electronics & Communication',
    'Information Technology',
    'Artificial Intelligence & Data Science',
    'Mechanical Engineering'
]

# =====================================================================
# 1. ADMIN DASHBOARD OVERVIEW
# =====================================================================
@admin_bp.route('/dashboard')
@login_required
@roles_required('Admin')
def dashboard():
    user = get_current_user()
    dept_filter = request.args.get('department')
    year_filter = request.args.get('academic_year', type=int)

    # Core Institutional KPIs
    total_students = Student.query.count()
    active_students = Student.query.filter_by(status='Active').count()
    total_faculty = User.query.filter_by(role='Faculty').count()
    total_depts = len(DEPARTMENTS)

    # Attendance Aggregate
    total_att_records = AttendanceRecord.query.count()
    present_att_records = AttendanceRecord.query.filter_by(status='Present').count()
    avg_attendance = round((present_att_records / total_att_records * 100), 1) if total_att_records > 0 else 0.0

    # Low attendance count (<75%)
    low_att_students = 0
    students_all = Student.query.all()
    for s in students_all:
        att = AttendanceService.calculate_student_attendance(s.student_id)
        if att['total_sessions'] > 0 and att['percentage'] < 75.0:
            low_att_students += 1

    # Academic Aggregate
    acad_records = AcademicRecord.query.all()
    avg_gpa = round(sum(a.gpa for a in acad_records) / len(acad_records), 2) if acad_records else 0.0

    # Risk Metrics
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    for s in students_all:
        eval_res = RiskAnalysisService.evaluate_student_risk(s)
        level = eval_res.get('risk_level')
        if level == 'High':
            high_risk_count += 1
        elif level == 'Medium':
            medium_risk_count += 1
        else:
            low_risk_count += 1

    # Placement Metrics
    placement_profiles = PlacementProfile.query.all()
    avg_readiness = round(sum(p.readiness_percentage for p in placement_profiles) / len(placement_profiles), 1) if placement_profiles else 0.0
    total_offers = PlacementOffer.query.count()
    placed_students_count = PlacementProfile.query.filter_by(placement_status='Placed').count()
    placement_rate = round((placed_students_count / len(placement_profiles) * 100), 1) if placement_profiles else 0.0

    # Department Breakdown
    dept_distribution = []
    for d in DEPARTMENTS:
        d_count = Student.query.filter_by(department=d).count()
        dept_distribution.append({'department': d, 'count': d_count})

    # Recent Audit Events
    recent_audits = AuditEvent.query.order_by(AuditEvent.timestamp.desc()).limit(10).all()

    # Interventions Summary
    open_interventions = Intervention.query.filter_by(status='Open').count()

    return render_template(
        'admin/dashboard.html',
        user=user,
        total_students=total_students,
        active_students=active_students,
        total_faculty=total_faculty,
        total_depts=total_depts,
        avg_attendance=avg_attendance,
        low_att_students=low_att_students,
        avg_gpa=avg_gpa,
        high_risk_count=high_risk_count,
        medium_risk_count=medium_risk_count,
        low_risk_count=low_risk_count,
        avg_readiness=avg_readiness,
        total_offers=total_offers,
        placement_rate=placement_rate,
        placed_students_count=placed_students_count,
        open_interventions=open_interventions,
        dept_distribution=dept_distribution,
        recent_audits=recent_audits,
        departments=DEPARTMENTS,
        last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

# =====================================================================
# 2. STUDENT MANAGEMENT
# =====================================================================
@admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def students():
    user = get_current_user()

    if request.method == 'POST':
        # Add new student
        stu_id = request.form.get('student_id', '').strip().upper()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        dept = request.form.get('department')
        year = int(request.form.get('academic_year', 1))
        sem = int(request.form.get('semester', 1))
        section = request.form.get('section', 'A').strip().upper()

        if not stu_id or not first_name or not last_name or not email:
            flash("All student fields are required.", "danger")
            return redirect(url_for('admin.students'))

        if Student.query.filter_by(student_id=stu_id).first():
            flash(f"Student ID {stu_id} already exists.", "danger")
            return redirect(url_for('admin.students'))

        if Student.query.filter_by(email=email).first():
            flash(f"Email {email} is already registered.", "danger")
            return redirect(url_for('admin.students'))

        new_stu = Student(
            student_id=stu_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=dept,
            academic_year=year,
            semester=sem,
            section=section,
            status='Active',
            enrollment_date=date.today()
        )
        db.session.add(new_stu)
        
        # Create Placement Profile automatically
        db.session.add(PlacementProfile(student_id=stu_id, target_role='Software Developer'))

        # Audit Event
        db.session.add(AuditEvent(
            user_id=user.id,
            action="CREATE_STUDENT",
            module="Student Management",
            details=f"Admin created student profile {stu_id} ({first_name} {last_name}).",
            ip_address=request.remote_addr
        ))

        db.session.commit()
        flash(f"Student {first_name} {last_name} ({stu_id}) successfully enrolled.", "success")
        return redirect(url_for('admin.students'))

    # GET Filter & Search
    q = request.args.get('q', '').strip()
    dept = request.args.get('department')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)

    query = Student.query
    if q:
        search_fmt = f"%{q}%"
        query = query.filter(
            (Student.first_name.ilike(search_fmt)) |
            (Student.last_name.ilike(search_fmt)) |
            (Student.student_id.ilike(search_fmt)) |
            (Student.email.ilike(search_fmt))
        )
    if dept:
        query = query.filter_by(department=dept)
    if status:
        query = query.filter_by(status=status)

    students_paginated = query.order_by(Student.student_id.asc()).paginate(page=page, per_page=20, error_out=False)

    return render_template(
        'admin/students.html',
        user=user,
        students=students_paginated.items,
        pagination=students_paginated,
        departments=DEPARTMENTS,
        selected_dept=dept,
        selected_status=status,
        search_query=q
    )

@admin_bp.route('/students/<student_id>/toggle-status', methods=['POST'])
@login_required
@roles_required('Admin')
def toggle_student_status(student_id):
    user = get_current_user()
    stu = Student.query.filter_by(student_id=student_id).first_or_404()
    new_status = 'Deactivated' if stu.status != 'Deactivated' else 'Active'
    stu.status = new_status

    db.session.add(AuditEvent(
        user_id=user.id,
        action="UPDATE_STUDENT_STATUS",
        module="Student Management",
        details=f"Admin changed student {student_id} status to {new_status}.",
        ip_address=request.remote_addr
    ))
    db.session.commit()
    flash(f"Student {stu.student_id} status changed to {new_status}.", "info")
    return redirect(url_for('admin.students'))

# =====================================================================
# 3. FACULTY MANAGEMENT
# =====================================================================
@admin_bp.route('/faculty', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def faculty():
    user = get_current_user()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        dept = request.form.get('department')
        password = request.form.get('password', 'Faculty@123')

        if not username or not full_name or not email:
            flash("Username, Full Name, and Email are required.", "danger")
            return redirect(url_for('admin.faculty'))

        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' already exists.", "danger")
            return redirect(url_for('admin.faculty'))

        new_faculty = User(
            username=username,
            full_name=full_name,
            email=email,
            department=dept,
            role='Faculty',
            is_active=True
        )
        new_faculty.set_password(password)
        db.session.add(new_faculty)

        db.session.add(AuditEvent(
            user_id=user.id,
            action="CREATE_FACULTY",
            module="Faculty Management",
            details=f"Admin created faculty account {username} ({full_name}) in {dept}.",
            ip_address=request.remote_addr
        ))
        db.session.commit()
        flash(f"Faculty member {full_name} successfully added.", "success")
        return redirect(url_for('admin.faculty'))

    faculty_list = User.query.filter_by(role='Faculty').order_by(User.full_name.asc()).all()
    
    # Calculate stats per faculty
    faculty_stats = []
    for f in faculty_list:
        assigned_students = Student.query.filter_by(mentor_id=f.id).count()
        sessions_taken = AttendanceSession.query.filter_by(faculty_id=f.id).count()
        interventions_count = Intervention.query.filter_by(faculty_id=f.id).count()
        faculty_stats.append({
            'faculty': f,
            'assigned_students': assigned_students,
            'sessions_taken': sessions_taken,
            'interventions_count': interventions_count
        })

    return render_template(
        'admin/faculty.html',
        user=user,
        faculty_stats=faculty_stats,
        departments=DEPARTMENTS
    )

@admin_bp.route('/faculty/<int:faculty_id>/toggle-status', methods=['POST'])
@login_required
@roles_required('Admin')
def toggle_faculty_status(faculty_id):
    user = get_current_user()
    fac = User.query.get_or_404(faculty_id)
    fac.is_active = not fac.is_active

    db.session.add(AuditEvent(
        user_id=user.id,
        action="TOGGLE_FACULTY_STATUS",
        module="Faculty Management",
        details=f"Admin toggled active status for faculty {fac.username} to {fac.is_active}.",
        ip_address=request.remote_addr
    ))
    db.session.commit()
    flash(f"Faculty member {fac.full_name} is now {'Active' if fac.is_active else 'Disabled'}.", "info")
    return redirect(url_for('admin.faculty'))

# =====================================================================
# 4. DEPARTMENT MANAGEMENT
# =====================================================================
@admin_bp.route('/departments')
@login_required
@roles_required('Admin')
def departments():
    user = get_current_user()
    dept_stats = []

    for d in DEPARTMENTS:
        students_count = Student.query.filter_by(department=d).count()
        faculty_count = User.query.filter_by(role='Faculty', department=d).count()
        
        # Dept attendance
        dept_sessions = AttendanceSession.query.filter_by(department=d).all()
        session_ids = [s.id for s in dept_sessions]
        if session_ids:
            total_records = AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(session_ids)).count()
            present_records = AttendanceRecord.query.filter(AttendanceRecord.session_id.in_(session_ids), AttendanceRecord.status == 'Present').count()
            dept_att = round((present_records / total_records * 100), 1) if total_records > 0 else 0.0
        else:
            dept_att = 82.5 # Default benchmark if no recorded sessions
        
        # Dept GPA
        dept_students = Student.query.filter_by(department=d).all()
        stu_ids = [s.student_id for s in dept_students]
        dept_acads = AcademicRecord.query.filter(AcademicRecord.student_id.in_(stu_ids)).all() if stu_ids else []
        avg_dept_gpa = round(sum(a.gpa for a in dept_acads) / len(dept_acads), 2) if dept_acads else 7.8

        dept_stats.append({
            'name': d,
            'students_count': students_count,
            'faculty_count': faculty_count,
            'avg_attendance': dept_att,
            'avg_gpa': avg_dept_gpa
        })

    return render_template(
        'admin/departments.html',
        user=user,
        dept_stats=dept_stats
    )

# =====================================================================
# 5. INSTITUTIONAL ATTENDANCE MANAGEMENT
# =====================================================================
@admin_bp.route('/attendance')
@login_required
@roles_required('Admin')
def attendance():
    user = get_current_user()
    dept = request.args.get('department')
    
    query = AttendanceSession.query
    if dept:
        query = query.filter_by(department=dept)
    
    recent_sessions = query.order_by(AttendanceSession.session_date.desc()).limit(30).all()
    
    # Low attendance list
    low_att_students = []
    for s in Student.query.all():
        att = AttendanceService.calculate_student_attendance(s.student_id)
        if att['total_sessions'] > 0 and att['percentage'] < 75.0:
            low_att_students.append({
                'student': s,
                'att': att
            })

    return render_template(
        'admin/attendance.html',
        user=user,
        recent_sessions=recent_sessions,
        low_att_students=low_att_students[:20],
        departments=DEPARTMENTS,
        selected_dept=dept
    )

# =====================================================================
# 6. ACADEMIC & RISK ANALYTICS
# =====================================================================
@admin_bp.route('/analytics')
@login_required
@roles_required('Admin')
def analytics():
    user = get_current_user()
    summary = InstitutionalAnalyticsService.get_dashboard_summary()
    return render_template(
        'admin/analytics.html',
        user=user,
        summary=summary,
        departments=DEPARTMENTS
    )

@admin_bp.route('/risk-analysis')
@login_required
@roles_required('Admin')
def risk_analysis():
    user = get_current_user()
    dept = request.args.get('department')
    
    all_students = Student.query.all()
    if dept:
        all_students = [s for s in all_students if s.department == dept]

    risk_evaluations = []
    high_count = 0
    med_count = 0
    low_count = 0

    for s in all_students:
        evaluation = RiskAnalysisService.evaluate_student_risk(s)
        level = evaluation['risk_level']
        if level == 'High':
            high_count += 1
        elif level == 'Medium':
            med_count += 1
        else:
            low_count += 1

        risk_evaluations.append({
            'student': s,
            'evaluation': evaluation
        })

    # Sort high risk first
    risk_evaluations.sort(key=lambda x: x['evaluation']['risk_score'], reverse=True)

    return render_template(
        'admin/risk_analysis.html',
        user=user,
        risk_evaluations=risk_evaluations[:50],
        high_count=high_count,
        med_count=med_count,
        low_count=low_count,
        total_evaluated=len(all_students),
        departments=DEPARTMENTS,
        selected_dept=dept
    )

# =====================================================================
# 7. FACULTY INTERVENTIONS & MENTORING OVERSIGHT
# =====================================================================
@admin_bp.route('/interventions')
@login_required
@roles_required('Admin')
def interventions():
    user = get_current_user()
    status_filter = request.args.get('status')
    
    query = Intervention.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    interventions_list = query.order_by(Intervention.session_date.desc()).all()
    open_count = Intervention.query.filter_by(status='Open').count()
    in_progress_count = Intervention.query.filter_by(status='In Progress').count()
    completed_count = Intervention.query.filter_by(status='Completed').count()

    return render_template(
        'admin/interventions.html',
        user=user,
        interventions=interventions_list,
        open_count=open_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        selected_status=status_filter
    )

# =====================================================================
# 8. PLACEMENT ANALYTICS (ADMIN VIEW)
# =====================================================================
@admin_bp.route('/placement-analytics')
@login_required
@roles_required('Admin')
def placement_analytics():
    user = get_current_user()
    
    companies = Company.query.all()
    jobs = JobOpportunity.query.all()
    applications = JobApplication.query.all()
    offers = PlacementOffer.query.all()
    profiles = PlacementProfile.query.all()

    avg_readiness = round(sum(p.readiness_percentage for p in profiles) / len(profiles), 1) if profiles else 0.0
    total_placed = len([p for p in profiles if p.placement_status == 'Placed'])
    placement_rate = round((total_placed / len(profiles) * 100), 1) if profiles else 0.0

    return render_template(
        'admin/placement.html',
        user=user,
        companies=companies,
        jobs=jobs,
        applications=applications,
        offers=offers,
        avg_readiness=avg_readiness,
        total_placed=total_placed,
        placement_rate=placement_rate
    )

# =====================================================================
# 9. USER ROLES & PERMISSIONS
# =====================================================================
@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def users():
    user = get_current_user()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'Faculty')
        dept = request.form.get('department')
        password = request.form.get('password', 'Password@123')

        if not username or not full_name or not email or not role:
            flash("All user fields are required.", "danger")
            return redirect(url_for('admin.users'))

        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken.", "danger")
            return redirect(url_for('admin.users'))

        new_user = User(
            username=username,
            full_name=full_name,
            email=email,
            role=role,
            department=dept if role in ['Faculty', 'Student'] else None,
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)

        db.session.add(AuditEvent(
            user_id=user.id,
            action="CREATE_USER",
            module="User Management",
            details=f"Admin created user account {username} with role {role}.",
            ip_address=request.remote_addr
        ))
        db.session.commit()
        flash(f"User account '{username}' ({role}) successfully created.", "success")
        return redirect(url_for('admin.users'))

    all_users = User.query.order_by(User.id.asc()).all()
    return render_template(
        'admin/users.html',
        user=user,
        users=all_users,
        departments=DEPARTMENTS
    )

# =====================================================================
# 10. AUDIT LOGS
# =====================================================================
@admin_bp.route('/audit-logs')
@login_required
@roles_required('Admin')
def audit_logs():
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    module_filter = request.args.get('module')

    query = AuditEvent.query
    if module_filter:
        query = query.filter_by(module=module_filter)

    logs_paginated = query.order_by(AuditEvent.timestamp.desc()).paginate(page=page, per_page=30, error_out=False)

    return render_template(
        'admin/audit_logs.html',
        user=user,
        logs=logs_paginated.items,
        pagination=logs_paginated,
        selected_module=module_filter
    )

# =====================================================================
# 11. REPORTS & CSV EXPORTS
# =====================================================================
@admin_bp.route('/reports')
@login_required
@roles_required('Admin')
def reports():
    user = get_current_user()
    return render_template('admin/reports.html', user=user)

@admin_bp.route('/reports/export/<report_type>')
@login_required
@roles_required('Admin')
def export_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'students':
        writer.writerow(['Student ID', 'First Name', 'Last Name', 'Email', 'Department', 'Year', 'Semester', 'Section', 'Status'])
        for s in Student.query.all():
            writer.writerow([s.student_id, s.first_name, s.last_name, s.email, s.department, s.academic_year, s.semester, s.section, s.status])
        filename = f"students_export_{date.today()}.csv"

    elif report_type == 'attendance':
        writer.writerow(['Student ID', 'Full Name', 'Department', 'Total Sessions', 'Present', 'Absent', 'On Leave', 'Attendance %'])
        for s in Student.query.all():
            att = AttendanceService.calculate_student_attendance(s.student_id)
            writer.writerow([s.student_id, s.full_name, s.department, att['total_sessions'], att['present'], att['absent'], att['on_leave'], att['percentage']])
        filename = f"attendance_summary_{date.today()}.csv"

    elif report_type == 'academics':
        writer.writerow(['Student ID', 'Full Name', 'Department', 'Semester', 'GPA', 'CGPA', 'Backlogs', 'Standing'])
        for a in AcademicRecord.query.all():
            writer.writerow([a.student_id, a.student.full_name if a.student else '', a.student.department if a.student else '', a.semester, a.gpa, a.cgpa, a.backlogs_count, a.academic_standing])
        filename = f"academic_performance_{date.today()}.csv"

    elif report_type == 'risk':
        writer.writerow(['Student ID', 'Full Name', 'Department', 'Risk Level', 'Risk Score', 'Factors'])
        for s in Student.query.all():
            eval_res = RiskAnalysisService.evaluate_student_risk(s)
            writer.writerow([s.student_id, s.full_name, s.department, eval_res['risk_level'], eval_res['risk_score'], "; ".join(eval_res['risk_factors'])])
        filename = f"student_risk_report_{date.today()}.csv"

    elif report_type == 'placement':
        writer.writerow(['Student ID', 'Full Name', 'Department', 'Target Role', 'Readiness %', 'Coding Score', 'Aptitude Score', 'Status'])
        for p in PlacementProfile.query.all():
            writer.writerow([p.student_id, p.student.full_name if p.student else '', p.student.department if p.student else '', p.target_role, p.readiness_percentage, p.coding_score, p.aptitude_score, p.placement_status])
        filename = f"placement_readiness_{date.today()}.csv"

    else:
        flash("Invalid report type.", "danger")
        return redirect(url_for('admin.reports'))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# =====================================================================
# 12. SYSTEM SETTINGS
# =====================================================================
@admin_bp.route('/settings')
@login_required
@roles_required('Admin')
def settings():
    user = get_current_user()
    weights = SuccessScoreService.get_weights()
    att_policy = AttendanceService.get_policy()
    risk_thresh = RiskAnalysisService.get_thresholds()
    audit_logs = AuditEvent.query.order_by(AuditEvent.timestamp.desc()).limit(30).all()

    return render_template(
        'settings.html',
        user=user,
        weights=weights,
        att_policy=att_policy,
        risk_thresh=risk_thresh,
        audit_logs=audit_logs
    )

@admin_bp.route('/settings/update-weights', methods=['POST'])
@login_required
@roles_required('Admin')
def update_weights():
    try:
        academic = float(request.form.get('weight_academic', 0.30))
        attendance = float(request.form.get('weight_attendance', 0.20))
        lms = float(request.form.get('weight_lms', 0.10))
        engagement = float(request.form.get('weight_engagement', 0.10))
        placement = float(request.form.get('weight_placement', 0.15))
        skills = float(request.form.get('weight_skills', 0.10))
        feedback = float(request.form.get('weight_feedback', 0.05))

        new_weights = {
            'academic': academic,
            'attendance': attendance,
            'lms': lms,
            'engagement': engagement,
            'placement': placement,
            'skills': skills,
            'feedback': feedback
        }

        if not SuccessScoreService.validate_weights(new_weights):
            flash("Validation error: Scoring weights must sum exactly to 1.0 (or 100%).", "danger")
            return redirect(url_for('admin.settings'))

        cfg = SystemConfig.query.filter_by(config_key='scoring_weights').first()
        if not cfg:
            cfg = SystemConfig(config_key='scoring_weights', config_value=json.dumps(new_weights), description="Composite scoring weights")
            db.session.add(cfg)
        else:
            cfg.config_value = json.dumps(new_weights)

        db.session.commit()
        SuccessScoreService.recalculate_all_scores()
        flash("Scoring weights successfully updated and student scores recalculated.", "success")
    except ValueError:
        flash("Invalid numeric format for weights.", "danger")

    return redirect(url_for('admin.settings'))

@admin_bp.route('/settings/update-thresholds', methods=['POST'])
@login_required
@roles_required('Admin')
def update_thresholds():
    try:
        att_warning = float(request.form.get('attendance_warning_threshold', 75.0))
        att_critical = float(request.form.get('attendance_critical_threshold', 65.0))
        risk_high = float(request.form.get('risk_high_threshold', 50.0))
        risk_med = float(request.form.get('risk_medium_threshold', 75.0))

        configs_to_update = [
            ('attendance_warning_threshold', str(att_warning)),
            ('attendance_critical_threshold', str(att_critical)),
            ('risk_high_threshold', str(risk_high)),
            ('risk_medium_threshold', str(risk_med)),
        ]

        for k, v in configs_to_update:
            cfg = SystemConfig.query.filter_by(config_key=k).first()
            if not cfg:
                db.session.add(SystemConfig(config_key=k, config_value=v))
            else:
                cfg.config_value = v

        db.session.commit()
        flash("Policy and risk thresholds updated successfully.", "success")
    except ValueError:
        flash("Invalid number entered for thresholds.", "danger")

    return redirect(url_for('admin.settings'))
