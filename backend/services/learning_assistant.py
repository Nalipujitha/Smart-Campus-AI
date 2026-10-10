from datetime import datetime
from backend.extensions import db
from backend.models.learning import LearningPlan, LearningTask, LmsActivity
from backend.models.academic import SubjectScore
from backend.models.student import Student

class LearningAssistantService:
    """
    Personalized Learning Assistant Service.
    Analyzes subject weak spots, generates custom learning plans and trackable weekly tasks.
    """

    LOCAL_RESOURCE_CATALOG = {
        'Data Structures': [
            {'title': 'Interactive Visual Algo & Tree Traversals', 'type': 'Interactive Tool', 'mins': 45},
            {'title': 'Graph Representation & Breadth/Depth First Search', 'type': 'Tutorial', 'mins': 60},
            {'title': 'Hash Tables & Collision Resolution Practice', 'type': 'Exercise', 'mins': 30}
        ],
        'Algorithms': [
            {'title': 'Divide & Conquer, Merge Sort Deep Dive', 'type': 'Reading', 'mins': 40},
            {'title': 'Dynamic Programming Memoization vs Tabulation', 'type': 'Code Lab', 'mins': 60},
            {'title': 'Greedy Algorithms vs Optimal Substructure Problems', 'type': 'Practice', 'mins': 45}
        ],
        'Database Management': [
            {'title': 'Relational Schema Normalization (1NF to 3NF/BCNF)', 'type': 'Tutorial', 'mins': 50},
            {'title': 'SQL Window Functions & Indexing Strategies', 'type': 'Code Lab', 'mins': 60},
            {'title': 'ACID Properties and Transaction Concurrency Control', 'type': 'Reading', 'mins': 40}
        ],
        'Operating Systems': [
            {'title': 'CPU Scheduling Algorithms & Simulation', 'type': 'Exercise', 'mins': 45},
            {'title': 'Virtual Memory, Paging, and Page Replacement', 'type': 'Tutorial', 'mins': 50},
            {'title': 'Deadlock Avoidance & Banker’s Algorithm Drill', 'type': 'Problem Set', 'mins': 40}
        ],
        'Computer Networks': [
            {'title': 'OSI vs TCP/IP Protocol Stack Breakdown', 'type': 'Reading', 'mins': 35},
            {'title': 'Subnet Masking & IP Routing Table Exercises', 'type': 'Exercise', 'mins': 45},
            {'title': 'HTTP, HTTPS, TLS Handshake & Socket Communication', 'type': 'Code Lab', 'mins': 50}
        ],
        'Web Development': [
            {'title': 'Modern CSS Grid & Responsive Layout Architecture', 'type': 'Exercise', 'mins': 40},
            {'title': 'JavaScript Asynchronous Promises & Async/Await Patterns', 'type': 'Code Lab', 'mins': 50},
            {'title': 'Building Secure RESTful APIs with Clean Architecture', 'type': 'Project', 'mins': 90}
        ],
        'Python Programming': [
            {'title': 'Pythonic Idioms, List Comprehensions & Generators', 'type': 'Tutorial', 'mins': 30},
            {'title': 'Object-Oriented Design & Magic Methods in Python', 'type': 'Exercise', 'mins': 45},
            {'title': 'Unit Testing with Pytest & Test-Driven Development', 'type': 'Code Lab', 'mins': 60}
        ]
    }

    @classmethod
    def get_subject_gaps(cls, student_id):
        """Identifies subjects where marks or quizzes are below threshold."""
        scores = SubjectScore.query.filter_by(student_id=student_id).all()
        weak_subjects = []
        for s in scores:
            pct = (s.marks_obtained / s.max_marks * 100) if s.max_marks else 0
            if pct < 65.0 or not s.is_passed:
                weak_subjects.append({
                    'subject_code': s.subject_code,
                    'subject_name': s.subject_name,
                    'percentage': round(pct, 1),
                    'grade': s.grade,
                    'is_passed': s.is_passed,
                    'severity': 'Critical' if pct < 50.0 else 'Moderate'
                })
        return weak_subjects

    @classmethod
    def create_study_plan(cls, student_id, skill_topic, weekly_hours=5.0):
        """Creates a structured learning plan with populated milestones."""
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return None

        # Determine resources
        resources = cls.LOCAL_RESOURCE_CATALOG.get(
            skill_topic,
            [
                {'title': f'Foundations of {skill_topic}', 'type': 'Reading', 'mins': 45},
                {'title': f'{skill_topic} Core Principles & Exercises', 'type': 'Exercise', 'mins': 60},
                {'title': f'{skill_topic} Capstone Practice Drill', 'type': 'Project', 'mins': 90}
            ]
        )

        plan = LearningPlan(
            student_id=student_id,
            title=f"Personalized Mastery Track: {skill_topic}",
            target_skill=skill_topic,
            weekly_goal_hours=weekly_hours,
            status='In Progress'
        )
        db.session.add(plan)
        db.session.flush()

        for res in resources:
            task = LearningTask(
                plan_id=plan.id,
                title=res['title'],
                description=f"Complete module on {skill_topic}. Format: {res['type']}.",
                resource_type=res['type'],
                estimated_minutes=res['mins'],
                is_completed=False
            )
            db.session.add(task)

        db.session.commit()
        return plan

    @classmethod
    def toggle_task_completion(cls, task_id, is_completed=True):
        """Marks a task as completed or incomplete and updates plan status."""
        task = LearningTask.query.get(task_id)
        if not task:
            return None, "Task not found."

        task.is_completed = is_completed
        task.completed_at = datetime.utcnow() if is_completed else None

        # Check if all tasks in plan completed
        plan = task.plan
        all_tasks = plan.tasks.all()
        if all(t.is_completed for t in all_tasks):
            plan.status = 'Completed'
        else:
            plan.status = 'In Progress'

        db.session.commit()
        return task, None
