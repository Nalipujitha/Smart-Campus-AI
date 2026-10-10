from datetime import datetime
from typing import Dict, Any, List, Optional

class MongoStudentSchema:
    """Schema and serializer for MongoDB Student Profiles collection ('students')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        if not data.get('first_name') or not data.get('last_name'):
            return False, "first_name and last_name are required"
        if not data.get('email') or '@' not in data.get('email'):
            return False, "valid email is required"
        if not data.get('department'):
            return False, "department is required"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'first_name': str(data.get('first_name', '')).strip(),
            'last_name': str(data.get('last_name', '')).strip(),
            'full_name': f"{data.get('first_name', '').strip()} {data.get('last_name', '').strip()}",
            'email': str(data.get('email', '')).strip().lower(),
            'department': str(data.get('department', '')).strip(),
            'academic_year': int(data.get('academic_year', 1)),
            'semester': int(data.get('semester', 1)),
            'section': str(data.get('section', 'A')).strip(),
            'status': str(data.get('status', 'Active')).strip(),
            'enrollment_date': data.get('enrollment_date'),
            'mentor_id': data.get('mentor_id'),
            'metadata': data.get('metadata', {}),
            'updated_at': datetime.utcnow()
        }


class MongoAcademicSchema:
    """Schema for Academic Performance records ('academic_records')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        if data.get('semester') is None:
            return False, "semester is required"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'semester': int(data.get('semester', 1)),
            'gpa': float(data.get('gpa', 0.0)),
            'cgpa': float(data.get('cgpa', data.get('gpa', 0.0))),
            'credits_completed': int(data.get('credits_completed', 20)),
            'total_credits': int(data.get('total_credits', 20)),
            'backlogs_count': int(data.get('backlogs_count', 0)),
            'academic_standing': str(data.get('academic_standing', 'Good')),
            'subject_scores': data.get('subject_scores', []), # list of subject score dicts
            'recorded_at': data.get('recorded_at', datetime.utcnow())
        }


class MongoAttendanceSchema:
    """Schema for Attendance Records collection ('attendance_records')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        if not data.get('status') or data.get('status') not in ['Present', 'Absent', 'On Leave']:
            return False, "status must be 'Present', 'Absent', or 'On Leave'"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'session_id': data.get('session_id'),
            'subject': str(data.get('subject', 'General Attendance')),
            'class_code': str(data.get('class_code', '')),
            'status': str(data.get('status', 'Present')),
            'remarks': data.get('remarks', ''),
            'session_date': data.get('session_date', datetime.utcnow().date().isoformat()),
            'recorded_at': datetime.utcnow()
        }


class MongoSkillsLearningSchema:
    """Schema for Skills, Learning Goals & LMS Activities ('skills_learning')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'target_role': str(data.get('target_role', 'Software Developer')),
            'technical_skills': data.get('technical_skills', []), # e.g. ['Python', 'SQL', 'DSA']
            'aptitude_score': float(data.get('aptitude_score', 0.0)),
            'coding_score': float(data.get('coding_score', 0.0)),
            'interview_score': float(data.get('interview_score', 0.0)),
            'readiness_percentage': float(data.get('readiness_percentage', 0.0)),
            'learning_plans': data.get('learning_plans', []),
            'lms_courses': data.get('lms_courses', []),
            'coding_problems_solved': int(data.get('coding_problems_solved', 0)),
            'updated_at': datetime.utcnow()
        }


class MongoFeedbackSchema:
    """Schema for Student Feedback records ('student_feedbacks')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'faculty_id': data.get('faculty_id'),
            'term': str(data.get('term', 'Current Semester')),
            'behavioral_score': float(data.get('behavioral_score', 85.0)),
            'punctuality_score': float(data.get('punctuality_score', 85.0)),
            'teamwork_score': float(data.get('teamwork_score', 85.0)),
            'initiative_score': float(data.get('initiative_score', 85.0)),
            'general_notes': str(data.get('general_notes', '')).strip(),
            'submitted_at': datetime.utcnow()
        }


class MongoRecommendationSchema:
    """Schema for AI-generated Recommendations ('ai_recommendations')."""
    @staticmethod
    def validate(data: Dict[str, Any]) -> (bool, Optional[str]):
        if not data.get('student_id'):
            return False, "student_id is required"
        if not data.get('title') or not data.get('suggested_action'):
            return False, "title and suggested_action are required"
        return True, None

    @staticmethod
    def format_document(data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'student_id': str(data.get('student_id', '')).strip().upper(),
            'title': str(data.get('title', '')).strip(),
            'category': str(data.get('category', 'Academic')),
            'priority': str(data.get('priority', 'Medium')),
            'reason': str(data.get('reason', '')).strip(),
            'suggested_action': str(data.get('suggested_action', '')).strip(),
            'responsible_role': str(data.get('responsible_role', 'Faculty Mentor')),
            'suggested_deadline': str(data.get('suggested_deadline', 'Within 7 days')),
            'status': str(data.get('status', 'Open')), # Open, In Progress, Completed
            'created_at': data.get('created_at', datetime.utcnow()),
            'updated_at': datetime.utcnow()
        }
