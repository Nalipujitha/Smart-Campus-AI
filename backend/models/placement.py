from datetime import datetime
from backend.extensions import db

class PlacementProfile(db.Model):
    __tablename__ = 'placement_profiles'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    target_role = db.Column(db.String(120), default='Software Developer')
    secondary_role = db.Column(db.String(120), nullable=True)
    aptitude_score = db.Column(db.Float, default=0.0) # 0 - 100
    coding_score = db.Column(db.Float, default=0.0) # 0 - 100
    communication_score = db.Column(db.Float, default=0.0) # 0 - 100
    interview_score = db.Column(db.Float, default=0.0) # 0 - 100
    resume_score = db.Column(db.Float, default=0.0) # 0 - 100
    readiness_percentage = db.Column(db.Float, default=0.0) # 0 - 100 calculated
    placement_status = db.Column(db.String(32), default='Seeking') # Seeking, Placed, Higher Studies, Entrepreneurship
    skills_json = db.Column(db.Text, nullable=True) # JSON string or comma-separated
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_readiness(self):
        # Weighted placement readiness score
        # Aptitude: 25%, Coding: 35%, Communication: 20%, Interview: 20%
        self.readiness_percentage = round(
            (self.aptitude_score * 0.25) +
            (self.coding_score * 0.35) +
            (self.communication_score * 0.20) +
            (self.interview_score * 0.20),
            1
        )
        return self.readiness_percentage

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'target_role': self.target_role,
            'secondary_role': self.secondary_role,
            'aptitude_score': self.aptitude_score,
            'coding_score': self.coding_score,
            'communication_score': self.communication_score,
            'interview_score': self.interview_score,
            'resume_score': self.resume_score,
            'readiness_percentage': self.readiness_percentage,
            'placement_status': self.placement_status,
            'skills_list': [s.strip() for s in self.skills_json.split(',')] if self.skills_json else [],
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PracticeQuestion(db.Model):
    __tablename__ = 'practice_questions'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(32), nullable=False, index=True) # Aptitude, Coding, Communication, Interview
    topic = db.Column(db.String(64), nullable=False)
    difficulty = db.Column(db.String(16), default='Medium') # Easy, Medium, Hard
    question_text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text, nullable=True) # JSON string for MCQs
    correct_answer = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    code_template = db.Column(db.Text, nullable=True)

    def to_dict(self):
        import json
        options = []
        if self.options_json:
            try:
                options = json.loads(self.options_json)
            except Exception:
                options = [o.strip() for o in self.options_json.split('|')]
        return {
            'id': self.id,
            'category': self.category,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'question_text': self.question_text,
            'options': options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'code_template': self.code_template
        }

class PracticeAttempt(db.Model):
    __tablename__ = 'practice_attempts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('practice_questions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    score_earned = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text, nullable=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    question = db.relationship('PracticeQuestion', backref='attempts')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'question_id': self.question_id,
            'question_text': self.question.question_text if self.question else '',
            'category': self.question.category if self.question else '',
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'score_earned': self.score_earned,
            'feedback': self.feedback,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None
        }


class Company(db.Model):
    __tablename__ = 'placement_companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False, index=True)
    industry = db.Column(db.String(64), nullable=False, default='Information Technology')
    website = db.Column(db.String(255), nullable=True)
    contact_person = db.Column(db.String(120), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(32), nullable=True)
    min_cgpa = db.Column(db.Float, default=6.0)
    eligible_departments = db.Column(db.String(255), default='Computer Science & Engineering,Information Technology')
    required_skills = db.Column(db.Text, nullable=True) # Python, SQL, DSA
    status = db.Column(db.String(32), default='Active') # Active, Inactive, Partner
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship('JobOpportunity', backref='company', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'website': self.website,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'min_cgpa': self.min_cgpa,
            'eligible_departments': [d.strip() for d in self.eligible_departments.split(',')] if self.eligible_departments else [],
            'required_skills': [s.strip() for s in self.required_skills.split(',')] if self.required_skills else [],
            'status': self.status,
            'jobs_count': len(self.jobs)
        }


class JobOpportunity(db.Model):
    __tablename__ = 'job_opportunities'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('placement_companies.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    role_type = db.Column(db.String(32), default='Full-time') # Full-time, Internship, Co-op
    location = db.Column(db.String(64), default='Bengaluru / Hybrid')
    ctc_package = db.Column(db.String(64), default='8.5 LPA')
    min_cgpa = db.Column(db.Float, default=6.5)
    min_readiness = db.Column(db.Float, default=60.0)
    eligible_departments = db.Column(db.String(255), default='Computer Science & Engineering,Information Technology,Artificial Intelligence & Data Science')
    required_skills = db.Column(db.Text, default='Python, Data Structures, SQL')
    application_deadline = db.Column(db.Date, nullable=True)
    drive_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(32), default='Active') # Active, Closed, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.name if self.company else 'Unknown',
            'title': self.title,
            'role_type': self.role_type,
            'location': self.location,
            'ctc_package': self.ctc_package,
            'min_cgpa': self.min_cgpa,
            'min_readiness': self.min_readiness,
            'eligible_departments': [d.strip() for d in self.eligible_departments.split(',')] if self.eligible_departments else [],
            'required_skills': self.required_skills,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'drive_date': self.drive_date.isoformat() if self.drive_date else None,
            'status': self.status,
            'applications_count': len(self.applications)
        }


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    __table_args__ = (
        db.UniqueConstraint('student_id', 'job_id', name='uq_student_job_application'),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_opportunities.id', ondelete='CASCADE'), nullable=False, index=True)
    stage = db.Column(db.String(32), default='Applied') # Applied, Shortlisted, Technical Assessment, Interview, Selected, Rejected, Offer Accepted
    round_cleared = db.Column(db.String(64), nullable=True)
    interview_date = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', backref='job_applications')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else self.student_id,
            'job_id': self.job_id,
            'job_title': self.job.title if self.job else '',
            'company_name': self.job.company.name if (self.job and self.job.company) else '',
            'stage': self.stage,
            'round_cleared': self.round_cleared,
            'feedback': self.feedback,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlacementOffer(db.Model):
    __tablename__ = 'placement_offers'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('placement_companies.id', ondelete='SET NULL'), nullable=True)
    company_name = db.Column(db.String(128), nullable=False)
    job_title = db.Column(db.String(128), nullable=False)
    ctc_package = db.Column(db.String(64), nullable=False) # e.g. 12.0 LPA
    ctc_numeric = db.Column(db.Float, default=6.0) # 12.0 for statistics
    offer_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(32), default='Offered') # Offered, Accepted, Declined
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='placement_offers')
    company = db.relationship('Company', backref='offers')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else self.student_id,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'ctc_package': self.ctc_package,
            'ctc_numeric': self.ctc_numeric,
            'offer_date': self.offer_date.isoformat() if self.offer_date else None,
            'status': self.status,
            'notes': self.notes
        }
