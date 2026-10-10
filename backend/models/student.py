from datetime import datetime
from backend.extensions import db

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), unique=True, nullable=False, index=True) # e.g. STU2024001
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(64), nullable=False, index=True) # Computer Science, Electronics, Information Tech, etc.
    academic_year = db.Column(db.Integer, nullable=False, default=1) # 1, 2, 3, 4
    semester = db.Column(db.Integer, nullable=False, default=1) # 1 - 8
    section = db.Column(db.String(8), nullable=True, default='A')
    enrollment_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='Active') # Active, At Risk, On Leave, Graduated
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_account = db.relationship('User', backref='student_profile', uselist=False, foreign_keys='User.student_id')
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    academic_records = db.relationship('AcademicRecord', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    subject_scores = db.relationship('SubjectScore', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    interventions = db.relationship('Intervention', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    lms_activities = db.relationship('LmsActivity', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    learning_plans = db.relationship('LearningPlan', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    placement_profile = db.relationship('PlacementProfile', backref='student', uselist=False, cascade='all, delete-orphan')
    practice_attempts = db.relationship('PracticeAttempt', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    engagement_records = db.relationship('EngagementRecord', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    feedback_records = db.relationship('FeedbackRecord', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    calculated_scores = db.relationship('StudentScore', backref='student', uselist=False, cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'department': self.department,
            'academic_year': self.academic_year,
            'semester': self.semester,
            'section': self.section,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'status': self.status,
            'mentor_id': self.mentor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
