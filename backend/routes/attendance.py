import io
import csv
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, session
from backend.extensions import db
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.student import Student
from backend.services.attendance_service import AttendanceService

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def index():
    user = get_current_user()
    if user.role == 'Student':
        return redirect(url_for('attendance.student_view', student_id=user.student_id))

    sessions = AttendanceSession.query.order_by(AttendanceSession.session_date.desc()).limit(20).all()
    summary = AttendanceService.get_attendance_summary()
    alerts = AttendanceService.get_attendance_alerts()

    departments = [
        'Computer Science & Engineering',
        'Electronics & Communication',
        'Information Technology',
        'Artificial Intelligence & Data Science',
        'Mechanical Engineering'
    ]

    return render_template(
        'attendance.html',
        user=user,
        sessions=sessions,
        summary=summary,
        alerts=alerts,
        departments=departments,
        today=date.today().isoformat()
    )

@attendance_bp.route('/roster')
@login_required
@roles_required('Admin', 'Faculty')
def get_roster():
    """AJAX endpoint to get eligible students for attendance recording."""
    department = request.args.get('department')
    semester = request.args.get('semester', type=int)

    query = Student.query.filter_by(status='Active')
    if department:
        query = query.filter_by(department=department)
    if semester:
        query = query.filter_by(semester=semester)

    students = query.order_by(Student.student_id.asc()).all()
    return jsonify([s.to_dict() for s in students])

@attendance_bp.route('/record', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def record_session():
    user = get_current_user()
    dept = request.form.get('department')
    sem = request.form.get('semester', type=int)
    subject = request.form.get('subject')
    class_code = request.form.get('class_code', f"{dept[:3].upper()}-SEM{sem}")
    session_date = request.form.get('session_date', date.today().isoformat())
    time_slot = request.form.get('time_slot', '09:00 - 10:00 AM')

    if not dept or not sem or not subject:
        flash("Department, semester, and subject are mandatory.", "danger")
        return redirect(url_for('attendance.index'))

    # Collect student statuses
    records_data = []
    for key, value in request.form.items():
        if key.startswith('status_'):
            stu_id = key.replace('status_', '')
            remarks = request.form.get(f'remarks_{stu_id}', '')
            records_data.append({
                'student_id': stu_id,
                'status': value,
                'remarks': remarks
            })

    if not records_data:
        flash("No student attendance marks submitted.", "warning")
        return redirect(url_for('attendance.index'))

    try:
        session_obj = AttendanceService.create_session_with_records(
            department=dept,
            class_code=class_code,
            semester=sem,
            subject=subject,
            session_date=session_date,
            faculty_id=user.id,
            records_data=records_data,
            time_slot=time_slot
        )
        flash(f"Attendance recorded successfully for {len(records_data)} students in {subject}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving attendance session: {str(e)}", "danger")

    return redirect(url_for('attendance.index'))

@attendance_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    session_obj = AttendanceSession.query.get_or_404(session_id)
    records = AttendanceRecord.query.filter_by(session_id=session_id).all()
    user = get_current_user()

    return render_template(
        'attendance_session_detail.html' if False else 'attendance.html',
        user=user,
        view_session=session_obj,
        session_records=records
    )

@attendance_bp.route('/reports')
@login_required
def reports():
    user = get_current_user()
    dept = request.args.get('department')
    sem = request.args.get('semester', type=int)
    subject = request.args.get('subject')

    summary = AttendanceService.get_attendance_summary()
    alerts = AttendanceService.get_attendance_alerts(department=dept, semester=sem)

    departments = [
        'Computer Science & Engineering',
        'Electronics & Communication',
        'Information Technology',
        'Artificial Intelligence & Data Science',
        'Mechanical Engineering'
    ]

    return render_template(
        'attendance_reports.html',
        user=user,
        summary=summary,
        alerts=alerts,
        departments=departments,
        selected_dept=dept,
        selected_sem=sem,
        selected_subject=subject
    )

@attendance_bp.route('/student/<student_id>')
@login_required
def student_view(student_id):
    user = get_current_user()
    if user.role == 'Student' and user.student_id != student_id:
        flash("Unauthorized: You can only view your own attendance records.", "danger")
        return redirect(url_for('attendance.student_view', student_id=user.student_id))

    student = Student.query.filter_by(student_id=student_id).first_or_404()
    stats = AttendanceService.calculate_student_attendance(student_id)
    
    # Detailed attendance history
    records = db.session.query(AttendanceRecord, AttendanceSession).join(
        AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id
    ).filter(
        AttendanceRecord.student_id == student_id
    ).order_by(AttendanceSession.session_date.desc()).all()

    return render_template(
        'attendance_reports.html',
        user=user,
        student=student,
        stats=stats,
        history=records,
        is_single_student=True
    )

@attendance_bp.route('/record/<int:record_id>/correct', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def correct_record(record_id):
    new_status = request.form.get('status')
    reason = request.form.get('correction_reason', '').strip()
    user = get_current_user()

    if not reason:
        flash("A valid correction reason is mandatory to edit attendance records.", "danger")
        return redirect(request.referrer or url_for('attendance.index'))

    record, err = AttendanceService.update_attendance_record(
        record_id=record_id,
        new_status=new_status,
        correction_reason=reason,
        user_id=user.id
    )

    if err:
        flash(err, "danger")
    else:
        flash(f"Attendance record corrected to '{new_status}' with logged audit trail.", "success")

    return redirect(request.referrer or url_for('attendance.index'))

@attendance_bp.route('/export')
@login_required
def export_csv():
    records = db.session.query(AttendanceRecord, AttendanceSession, Student).join(
        AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id
    ).join(
        Student, AttendanceRecord.student_id == Student.student_id
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Session ID', 'Session Date', 'Department', 'Semester', 'Subject', 'Student ID', 'Student Name', 'Status', 'Remarks', 'Correction Reason'])

    for rec, sess, stu in records:
        writer.writerow([
            sess.id,
            sess.session_date.isoformat(),
            sess.department,
            sess.semester,
            sess.subject,
            stu.student_id,
            stu.full_name,
            rec.status,
            rec.remarks or '',
            rec.correction_reason or ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=campus_attendance_export.csv"}
    )
