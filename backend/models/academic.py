from datetime import datetime
from backend.extensions import db

class AcademicRecord(db.Model):
    __tablename__ = 'academic_records'
    __table_args__ = (
        db.UniqueConstraint('student_id', 'semester', name='uq_student_semester_academic'),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False)
    gpa = db.Column(db.Float, nullable=False) # e.g. 8.4 (out of 10)
    cgpa = db.Column(db.Float, nullable=True) # cumulative gpa
    credits_completed = db.Column(db.Integer, nullable=False, default=20)
    total_credits = db.Column(db.Integer, nullable=False, default=20)
    backlogs_count = db.Column(db.Integer, nullable=False, default=0)
    academic_standing = db.Column(db.String(32), default='Good') # Good, Probation, Dean's List, At Risk
    exam_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'semester': self.semester,
            'gpa': self.gpa,
            'cgpa': self.cgpa,
            'credits_completed': self.credits_completed,
            'total_credits': self.total_credits,
            'backlogs_count': self.backlogs_count,
            'academic_standing': self.academic_standing,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SubjectScore(db.Model):
    __tablename__ = 'subject_scores'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False)
    subject_code = db.Column(db.String(32), nullable=False)
    subject_name = db.Column(db.String(120), nullable=False)
    internal_marks = db.Column(db.Float, nullable=True, default=0) # out of 30 or 40
    external_marks = db.Column(db.Float, nullable=True, default=0) # out of 70 or 60
    marks_obtained = db.Column(db.Float, nullable=False) # total marks out of 100
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    grade = db.Column(db.String(4), nullable=True) # O, A+, A, B+, B, C, F
    is_passed = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'semester': self.semester,
            'subject_code': self.subject_code,
            'subject_name': self.subject_name,
            'internal_marks': self.internal_marks,
            'external_marks': self.external_marks,
            'marks_obtained': self.marks_obtained,
            'max_marks': self.max_marks,
            'percentage': round((self.marks_obtained / self.max_marks * 100), 1) if self.max_marks else 0,
            'grade': self.grade,
            'is_passed': self.is_passed
        }
