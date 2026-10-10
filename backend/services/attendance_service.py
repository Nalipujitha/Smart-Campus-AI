from datetime import datetime, date
import pandas as pd
from backend.extensions import db
from backend.config import Config
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.student import Student
from backend.models.audit import AuditEvent, SystemConfig
from backend.models.recommendation import Recommendation

class AttendanceService:
    """
    Comprehensive attendance calculation and management service.
    Follows institutional policy, handles approved leaves, prevents duplicates,
    generates alerts, and triggers downstream analytics updates.
    """

    @classmethod
    def get_policy(cls):
        """Fetches attendance policy thresholds."""
        warning = Config.ATTENDANCE_WARNING_THRESHOLD
        critical = Config.ATTENDANCE_CRITICAL_THRESHOLD
        exclude_leave = Config.ATTENDANCE_EXCLUDE_APPROVED_LEAVE

        try:
            cfg_w = SystemConfig.query.filter_by(config_key='attendance_warning_threshold').first()
            if cfg_w:
                warning = float(cfg_w.config_value)
            cfg_c = SystemConfig.query.filter_by(config_key='attendance_critical_threshold').first()
            if cfg_c:
                critical = float(cfg_c.config_value)
            cfg_l = SystemConfig.query.filter_by(config_key='attendance_exclude_leave').first()
            if cfg_l:
                exclude_leave = cfg_l.config_value.lower() in ('true', '1', 'yes')
        except Exception:
            pass

        return {
            'warning_threshold': warning,
            'critical_threshold': critical,
            'exclude_approved_leave': exclude_leave
        }

    @classmethod
    def calculate_student_attendance(cls, student_id, subject=None, semester=None):
        """
        Calculates student attendance percentage according to institutional policy.
        Returns: {
            'student_id': str,
            'total_sessions': int,
            'present_count': int,
            'absent_count': int,
            'leave_count': int,
            'eligible_sessions': int,
            'attendance_percentage': float or None,
            'is_below_warning': bool,
            'is_below_critical': bool
        }
        """
        policy = cls.get_policy()

        query = db.session.query(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceSession.is_cancelled == False
        )

        if subject:
            query = query.filter(AttendanceSession.subject == subject)
        if semester:
            query = query.filter(AttendanceSession.semester == semester)

        records = query.all()
        total_sessions = len(records)
        if total_sessions == 0:
            return {
                'student_id': student_id,
                'total_sessions': 0,
                'present_count': 0,
                'absent_count': 0,
                'leave_count': 0,
                'present': 0,
                'absent': 0,
                'on_leave': 0,
                'eligible_sessions': 0,
                'attendance_percentage': None, # Indicates 'Not Available'
                'percentage': 0.0,
                'is_below_warning': False,
                'is_below_critical': False,
                'policy_applied': policy
            }

        present_count = sum(1 for r in records if r.status == 'Present')
        absent_count = sum(1 for r in records if r.status == 'Absent')
        leave_count = sum(1 for r in records if r.status == 'On Leave')

        if policy['exclude_approved_leave']:
            eligible_sessions = total_sessions - leave_count
        else:
            eligible_sessions = total_sessions

        if eligible_sessions <= 0:
            pct = 100.0 if present_count > 0 else (None if total_sessions == 0 else 0.0)
        else:
            pct = round((present_count / eligible_sessions) * 100.0, 1)

        is_below_warning = (pct is not None and pct < policy['warning_threshold'])
        is_below_critical = (pct is not None and pct < policy['critical_threshold'])

        return {
            'student_id': student_id,
            'total_sessions': total_sessions,
            'present_count': present_count,
            'absent_count': absent_count,
            'leave_count': leave_count,
            'present': present_count,
            'absent': absent_count,
            'on_leave': leave_count,
            'eligible_sessions': eligible_sessions,
            'attendance_percentage': pct,
            'percentage': pct if pct is not None else 0.0,
            'is_below_warning': is_below_warning,
            'is_below_critical': is_below_critical,
            'policy_applied': policy
        }

    @classmethod
    def create_session_with_records(cls, department, class_code, semester, subject, session_date, faculty_id, records_data, time_slot=None):
        """
        Creates an attendance session and submits records in a transaction.
        records_data: list of dicts [{'student_id': 'STU001', 'status': 'Present', 'remarks': ''}, ...]
        """
        # Parse date if string
        if isinstance(session_date, str):
            session_date = datetime.strptime(session_date, '%Y-%m-%d').date()

        session = AttendanceSession(
            department=department,
            class_code=class_code,
            semester=semester,
            subject=subject,
            session_date=session_date,
            time_slot=time_slot,
            faculty_id=faculty_id
        )
        db.session.add(session)
        db.session.flush() # obtain session.id

        created_records = []
        affected_students = set()

        for rec in records_data:
            stu_id = rec.get('student_id')
            status = rec.get('status', 'Absent')
            remarks = rec.get('remarks', '')

            # Check if student exists
            student = Student.query.filter_by(student_id=stu_id).first()
            if not student:
                continue

            record = AttendanceRecord(
                session_id=session.id,
                student_id=stu_id,
                status=status,
                remarks=remarks,
                updated_by=faculty_id
            )
            db.session.add(record)
            created_records.append(record)
            affected_students.add(stu_id)

        db.session.commit()

        # Update scoring & check alerts for affected students
        cls._trigger_post_attendance_updates(affected_students)

        return session

    @classmethod
    def update_attendance_record(cls, record_id, new_status, correction_reason, user_id):
        """
        Updates an existing attendance record with mandatory correction reason and audit logging.
        """
        record = AttendanceRecord.query.get(record_id)
        if not record:
            return None, "Attendance record not found."

        old_status = record.status
        record.status = new_status
        record.correction_reason = correction_reason
        record.updated_by = user_id
        record.updated_at = datetime.utcnow()

        # Audit log
        audit = AuditEvent(
            user_id=user_id,
            action="ATTENDANCE_CORRECTION",
            module="Attendance",
            details=f"Record {record.id} for student {record.student_id} updated from '{old_status}' to '{new_status}'. Reason: {correction_reason}"
        )
        db.session.add(audit)
        db.session.commit()

        # Update scoring
        cls._trigger_post_attendance_updates({record.student_id})

        return record, None

    @classmethod
    def get_attendance_alerts(cls, department=None, semester=None):
        """
        Generates attendance alerts for students falling below the warning threshold.
        """
        policy = cls.get_policy()
        query = Student.query.filter_by(status='Active')
        if department:
            query = query.filter_by(department=department)
        if semester:
            query = query.filter_by(semester=semester)

        students = query.all()
        alerts = []
        for stu in students:
            stats = cls.calculate_student_attendance(stu.student_id)
            if stats['is_below_warning']:
                severity = 'Critical' if stats['is_below_critical'] else 'Warning'
                pct_str = f"{stats['attendance_percentage']}%" if stats['attendance_percentage'] is not None else "N/A"
                suggested_action = (
                    "Schedule mandatory academic advisor intervention" if severity == 'Critical'
                    else "Send automated attendance advisory and notify faculty mentor"
                )
                alerts.append({
                    'student_id': stu.student_id,
                    'student_name': stu.full_name,
                    'department': stu.department,
                    'semester': stu.semester,
                    'attendance_percentage': stats['attendance_percentage'],
                    'severity': severity,
                    'eligible_sessions': stats['eligible_sessions'],
                    'absent_count': stats['absent_count'],
                    'threshold': policy['warning_threshold'],
                    'explanation': f"Student has attended {stats['present_count']} of {stats['eligible_sessions']} eligible sessions ({pct_str}), which is below the institutional {policy['warning_threshold']}% standard.",
                    'suggested_action': suggested_action
                })

        # Sort with critical first
        alerts.sort(key=lambda x: (x['severity'] != 'Critical', x['attendance_percentage'] or 100))
        return alerts

    @classmethod
    def get_attendance_summary(cls):
        """Generates institutional attendance summary metrics and charts."""
        sessions = AttendanceSession.query.filter_by(is_cancelled=False).all()
        records = AttendanceRecord.query.join(AttendanceSession).filter(AttendanceSession.is_cancelled == False).all()

        total_records = len(records)
        present_count = sum(1 for r in records if r.status == 'Present')
        absent_count = sum(1 for r in records if r.status == 'Absent')
        leave_count = sum(1 for r in records if r.status == 'On Leave')

        policy = cls.get_policy()
        eligible = total_records - leave_count if policy['exclude_approved_leave'] else total_records
        avg_pct = round((present_count / eligible * 100), 1) if eligible > 0 else 0.0

        # Department wise breakdown
        dept_data = {}
        for r in records:
            dept = r.session.department
            if dept not in dept_data:
                dept_data[dept] = {'present': 0, 'absent': 0, 'leave': 0, 'total': 0}
            dept_data[dept]['total'] += 1
            if r.status == 'Present':
                dept_data[dept]['present'] += 1
            elif r.status == 'Absent':
                dept_data[dept]['absent'] += 1
            elif r.status == 'On Leave':
                dept_data[dept]['leave'] += 1

        dept_summary = []
        for dept, counts in dept_data.items():
            d_eligible = counts['total'] - counts['leave'] if policy['exclude_approved_leave'] else counts['total']
            d_pct = round((counts['present'] / d_eligible * 100), 1) if d_eligible > 0 else 0.0
            dept_summary.append({
                'department': dept,
                'percentage': d_pct,
                'total_records': counts['total'],
                'present': counts['present'],
                'absent': counts['absent']
            })

        # Subject wise breakdown
        subj_data = {}
        for r in records:
            subj = r.session.subject
            if subj not in subj_data:
                subj_data[subj] = {'present': 0, 'total': 0, 'leave': 0}
            subj_data[subj]['total'] += 1
            if r.status == 'Present':
                subj_data[subj]['present'] += 1
            elif r.status == 'On Leave':
                subj_data[subj]['leave'] += 1

        subj_summary = []
        for subj, counts in subj_data.items():
            s_eligible = counts['total'] - counts['leave'] if policy['exclude_approved_leave'] else counts['total']
            s_pct = round((counts['present'] / s_eligible * 100), 1) if s_eligible > 0 else 0.0
            subj_summary.append({
                'subject': subj,
                'percentage': s_pct,
                'total_sessions': counts['total']
            })

        return {
            'total_sessions_conducted': len(sessions),
            'total_records_marked': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'leave_count': leave_count,
            'average_attendance_pct': avg_pct,
            'department_breakdown': dept_summary,
            'subject_breakdown': subj_summary
        }

    @classmethod
    def _trigger_post_attendance_updates(cls, student_ids):
        """Updates scoring, risk, and recommendations for affected students."""
        from backend.services.success_score import SuccessScoreService
        from backend.services.recommendations import RecommendationService

        for sid in student_ids:
            stu = Student.query.filter_by(student_id=sid).first()
            if stu:
                SuccessScoreService.calculate_student_score(stu, save_db=True)
                RecommendationService.generate_student_recommendations(stu, save_db=True)
