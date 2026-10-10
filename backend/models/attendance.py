from datetime import datetime, date
from backend.extensions import db

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'

    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(64), nullable=False, index=True)
    class_code = db.Column(db.String(32), nullable=False) # e.g. CSE-SEM5-A
    semester = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(120), nullable=False, index=True)
    session_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    time_slot = db.Column(db.String(32), nullable=True) # e.g. 09:00 - 10:00 AM
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_cancelled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    records = db.relationship('AttendanceRecord', backref='session', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'department': self.department,
            'class_code': self.class_code,
            'semester': self.semester,
            'subject': self.subject,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'time_slot': self.time_slot,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.full_name if self.faculty else 'Unassigned',
            'is_cancelled': self.is_cancelled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_students': self.records.count(),
            'present_count': self.records.filter_by(status='Present').count(),
            'absent_count': self.records.filter_by(status='Absent').count(),
            'leave_count': self.records.filter_by(status='On Leave').count()
        }

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='uq_session_student_attendance'),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False) # 'Present', 'Absent', 'On Leave'
    remarks = db.Column(db.String(255), nullable=True)
    correction_reason = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'status': self.status,
            'remarks': self.remarks,
            'correction_reason': self.correction_reason,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
