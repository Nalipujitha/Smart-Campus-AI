from datetime import datetime, date
from backend.extensions import db

class Intervention(db.Model):
    __tablename__ = 'interventions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=False, default='Academic') # Academic, Attendance, Placement, Personal, Skills
    priority = db.Column(db.String(16), nullable=False, default='Medium') # High, Medium, Low
    status = db.Column(db.String(32), nullable=False, default='Open') # Open, In Progress, Completed, Cancelled
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    follow_up_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=False)
    action_items = db.Column(db.Text, nullable=True)
    outcome_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_overdue(self):
        if self.status in ['Completed', 'Cancelled'] or not self.follow_up_date:
            return False
        return self.follow_up_date < date.today()

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else 'Unknown',
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.full_name if self.faculty else 'Unassigned Advisor',
            'title': self.title,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'is_overdue': self.is_overdue,
            'notes': self.notes,
            'action_items': self.action_items,
            'outcome_notes': self.outcome_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
