import json
from datetime import datetime
from backend.extensions import db

class CodingProblem(db.Model):
    __tablename__ = 'coding_problems'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    difficulty = db.Column(db.String(16), nullable=False, default='Easy') # Easy, Medium, Hard
    topic = db.Column(db.String(64), nullable=False, default='Arrays')
    description_markdown = db.Column(db.Text, nullable=False)
    input_format = db.Column(db.Text, nullable=True)
    output_format = db.Column(db.Text, nullable=True)
    constraints = db.Column(db.Text, nullable=True)
    sample_input = db.Column(db.Text, nullable=True)
    sample_output = db.Column(db.Text, nullable=True)
    starter_code_json = db.Column(db.Text, nullable=True) # Dict of {python: "...", java: "...", cpp: "..."}
    test_cases_json = db.Column(db.Text, nullable=False) # List of {"input": "...", "expected_output": "...", "is_hidden": bool}
    points = db.Column(db.Integer, default=10, nullable=False)
    time_limit_sec = db.Column(db.Float, default=3.0, nullable=False)
    memory_limit_mb = db.Column(db.Integer, default=128, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submissions = db.relationship('CodingSubmission', backref='problem', lazy=True, cascade='all, delete-orphan')
    drafts = db.relationship('StudentCodeDraft', backref='problem', lazy=True, cascade='all, delete-orphan')

    def get_starter_code(self, language='python'):
        if not self.starter_code_json:
            return "# Write your solution here\n"
        try:
            starters = json.loads(self.starter_code_json)
            return starters.get(language, starters.get('python', "# Write your solution here\n"))
        except Exception:
            return "# Write your solution here\n"

    def get_test_cases(self):
        if not self.test_cases_json:
            return []
        try:
            return json.loads(self.test_cases_json)
        except Exception:
            return []

    def get_public_test_cases(self):
        cases = self.get_test_cases()
        return [c for c in cases if not c.get('is_hidden', False)]

    def to_dict(self, include_test_cases=False):
        data = {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'difficulty': self.difficulty,
            'topic': self.topic,
            'description_markdown': self.description_markdown,
            'input_format': self.input_format,
            'output_format': self.output_format,
            'constraints': self.constraints,
            'sample_input': self.sample_input,
            'sample_output': self.sample_output,
            'starter_code': self.get_starter_code(),
            'points': self.points,
            'time_limit_sec': self.time_limit_sec,
            'public_test_cases': self.get_public_test_cases()
        }
        if include_test_cases:
            data['all_test_cases'] = self.get_test_cases()
        return data


class StudentCodeDraft(db.Model):
    __tablename__ = 'student_code_drafts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('coding_problems.id', ondelete='CASCADE'), nullable=False, index=True)
    language = db.Column(db.String(16), default='python', nullable=False)
    code = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'problem_id', 'language', name='uq_student_problem_lang_draft'),
    )


class CodingSubmission(db.Model):
    __tablename__ = 'coding_submissions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('coding_problems.id', ondelete='CASCADE'), nullable=False, index=True)
    language = db.Column(db.String(16), default='python', nullable=False)
    code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False) # 'Accepted', 'Wrong Answer', 'Time Limit Exceeded', 'Runtime Error', 'Compilation Error'
    passed_test_cases = db.Column(db.Integer, default=0, nullable=False)
    total_test_cases = db.Column(db.Integer, default=0, nullable=False)
    score = db.Column(db.Float, default=0.0, nullable=False)
    execution_time_ms = db.Column(db.Float, default=0.0)
    memory_kb = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'problem_id': self.problem_id,
            'problem_title': self.problem.title if self.problem else None,
            'problem_slug': self.problem.slug if self.problem else None,
            'language': self.language,
            'code': self.code,
            'status': self.status,
            'passed_test_cases': self.passed_test_cases,
            'total_test_cases': self.total_test_cases,
            'score': self.score,
            'execution_time_ms': self.execution_time_ms,
            'error_message': self.error_message,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }
