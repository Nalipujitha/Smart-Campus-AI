from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(32), nullable=False, default='Student') # Admin, Faculty, Placement_Officer, Student
    department = db.Column(db.String(64), nullable=True) # CSE, ECE, MECH, CIVIL, IT, AI_DS, MANAGEMENT
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='SET NULL'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    interventions_conducted = db.relationship('Intervention', backref='faculty', lazy=True, foreign_keys='Intervention.faculty_id')
    sessions_recorded = db.relationship('AttendanceSession', backref='faculty', lazy=True, foreign_keys='AttendanceSession.faculty_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'student_id': self.student_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
