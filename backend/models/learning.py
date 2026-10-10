from datetime import datetime
from backend.extensions import db

class LmsActivity(db.Model):
    __tablename__ = 'lms_activities'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    course_name = db.Column(db.String(120), nullable=False)
    course_code = db.Column(db.String(32), nullable=True)
    modules_completed = db.Column(db.Integer, nullable=False, default=0)
    total_modules = db.Column(db.Integer, nullable=False, default=10)
    time_spent_hours = db.Column(db.Float, nullable=False, default=0.0)
    quiz_score_avg = db.Column(db.Float, nullable=False, default=0.0) # 0 - 100
    assignment_submission_rate = db.Column(db.Float, nullable=True, default=100.0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def completion_percentage(self):
        return round((self.modules_completed / self.total_modules * 100), 1) if self.total_modules else 0

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_name': self.course_name,
            'course_code': self.course_code,
            'modules_completed': self.modules_completed,
            'total_modules': self.total_modules,
            'completion_percentage': self.completion_percentage,
            'time_spent_hours': self.time_spent_hours,
            'quiz_score_avg': self.quiz_score_avg,
            'assignment_submission_rate': self.assignment_submission_rate,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }

class LearningPlan(db.Model):
    __tablename__ = 'learning_plans'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    target_skill = db.Column(db.String(120), nullable=False)
    weekly_goal_hours = db.Column(db.Float, default=5.0)
    status = db.Column(db.String(32), default='In Progress') # In Progress, Completed, Paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('LearningTask', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def progress_percentage(self):
        total = self.tasks.count()
        if not total:
            return 0
        done = self.tasks.filter_by(is_completed=True).count()
        return round((done / total * 100), 1)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'target_skill': self.target_skill,
            'weekly_goal_hours': self.weekly_goal_hours,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'tasks_count': self.tasks.count(),
            'tasks_completed': self.tasks.filter_by(is_completed=True).count(),
            'tasks': [t.to_dict() for t in self.tasks],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LearningTask(db.Model):
    __tablename__ = 'learning_tasks'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('learning_plans.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource_type = db.Column(db.String(32), default='Article') # Video, Exercise, Reading, Project
    estimated_minutes = db.Column(db.Integer, default=30)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'title': self.title,
            'description': self.description,
            'resource_type': self.resource_type,
            'estimated_minutes': self.estimated_minutes,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
