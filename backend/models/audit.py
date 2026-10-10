from datetime import datetime
from backend.extensions import db

class AuditEvent(db.Model):
    __tablename__ = 'audit_events'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(64), nullable=False) # LOGIN, ATTENDANCE_CORRECTION, INTERVENTION_CREATE, etc.
    module = db.Column(db.String(64), nullable=False) # Auth, Attendance, Students, Analytics, Settings
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref='audit_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'System',
            'action': self.action,
            'module': self.module,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class CampusKnowledge(db.Model):
    __tablename__ = 'campus_knowledge'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), nullable=False, index=True) # Academic, Attendance, Examination, Library, Placement, Mentoring, Facilities
    topic = db.Column(db.String(120), nullable=False)
    keywords = db.Column(db.String(255), nullable=False) # comma-separated search terms
    content = db.Column(db.Text, nullable=False)
    contact_person = db.Column(db.String(120), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    is_verified = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'topic': self.topic,
            'keywords': self.keywords,
            'content': self.content,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'is_verified': self.is_verified,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EngagementRecord(db.Model):
    __tablename__ = 'engagement_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    activity_type = db.Column(db.String(64), nullable=False) # Hackathon, Workshop, Club, Sports, Seminar, Certification
    title = db.Column(db.String(255), nullable=False)
    participation_level = db.Column(db.String(32), default='Participant') # Participant, Winner, Organizer, Member
    score_points = db.Column(db.Float, default=10.0) # 0 - 100 points
    event_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'activity_type': self.activity_type,
            'title': self.title,
            'participation_level': self.participation_level,
            'score_points': self.score_points,
            'event_date': self.event_date.isoformat() if self.event_date else None
        }

class FeedbackRecord(db.Model):
    __tablename__ = 'feedback_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    behavioral_score = db.Column(db.Float, default=80.0) # 0 - 100
    punctuality_score = db.Column(db.Float, default=80.0)
    teamwork_score = db.Column(db.Float, default=80.0)
    initiative_score = db.Column(db.Float, default=80.0)
    general_notes = db.Column(db.Text, nullable=True)
    term = db.Column(db.String(32), default='Midterm')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def average_score(self):
        return round((self.behavioral_score + self.punctuality_score + self.teamwork_score + self.initiative_score) / 4.0, 1)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'faculty_id': self.faculty_id,
            'behavioral_score': self.behavioral_score,
            'punctuality_score': self.punctuality_score,
            'teamwork_score': self.teamwork_score,
            'initiative_score': self.initiative_score,
            'average_score': self.average_score,
            'general_notes': self.general_notes,
            'term': self.term,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StudentScore(db.Model):
    __tablename__ = 'student_scores'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    
    # Normalized component scores (0-100)
    academic_component = db.Column(db.Float, default=0.0)
    attendance_component = db.Column(db.Float, default=0.0)
    lms_component = db.Column(db.Float, default=0.0)
    engagement_component = db.Column(db.Float, default=0.0)
    placement_component = db.Column(db.Float, default=0.0)
    skills_component = db.Column(db.Float, default=0.0)
    feedback_component = db.Column(db.Float, default=0.0)
    
    # Overall calculated composite score (0-100)
    success_score = db.Column(db.Float, default=0.0)
    
    # Risk Classification
    risk_level = db.Column(db.String(32), default='Low') # 'Low', 'Medium', 'High'
    risk_factors_json = db.Column(db.Text, nullable=True) # JSON of specific triggers
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        factors = []
        if self.risk_factors_json:
            try:
                factors = json.loads(self.risk_factors_json)
            except Exception:
                factors = []
        return {
            'student_id': self.student_id,
            'academic_component': round(self.academic_component, 1),
            'attendance_component': round(self.attendance_component, 1),
            'lms_component': round(self.lms_component, 1),
            'engagement_component': round(self.engagement_component, 1),
            'placement_component': round(self.placement_component, 1),
            'skills_component': round(self.skills_component, 1),
            'feedback_component': round(self.feedback_component, 1),
            'success_score': round(self.success_score, 1),
            'risk_level': self.risk_level,
            'risk_factors': factors,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }

class SystemConfig(db.Model):
    __tablename__ = 'system_configs'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(64), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
