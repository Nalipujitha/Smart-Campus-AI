from datetime import datetime
from backend.extensions import db

class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), nullable=False, default='Academic') # Academic, Attendance, Career, Learning, Placement, Skills
    priority = db.Column(db.String(16), nullable=False, default='Medium') # High, Medium, Low
    reason = db.Column(db.Text, nullable=False)
    trigger_data = db.Column(db.Text, nullable=True) # e.g. "Attendance: 68.5% (Threshold 75%)"
    suggested_action = db.Column(db.Text, nullable=False)
    responsible_role = db.Column(db.String(120), nullable=True, default='Faculty Mentor')
    suggested_deadline = db.Column(db.String(64), nullable=True, default='Within 7 days')
    status = db.Column(db.String(32), default='Active') # Active, In Progress, Completed, Dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'category': self.category,
            'priority': self.priority,
            'reason': self.reason,
            'trigger_data': self.trigger_data,
            'suggested_action': self.suggested_action,
            'responsible_role': self.responsible_role or 'Faculty Mentor',
            'suggested_deadline': self.suggested_deadline or 'Within 7 days',
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
