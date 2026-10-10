from backend.models.user import User
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.intervention import Intervention
from backend.models.recommendation import Recommendation
from backend.models.learning import LmsActivity, LearningPlan, LearningTask
from backend.models.placement import (
    PlacementProfile, PracticeQuestion, PracticeAttempt,
    Company, JobOpportunity, JobApplication, PlacementOffer
)
from backend.models.audit import AuditEvent, CampusKnowledge, EngagementRecord, FeedbackRecord, StudentScore, SystemConfig
from backend.models.coding import CodingProblem, StudentCodeDraft, CodingSubmission
from backend.models.student_files import StudentFile, StudentFileVersion, StudentWorkspaceSetting, detect_language
from backend.models.chat import ChatConversation, ChatMessage

__all__ = [
    'User',
    'Student',
    'AttendanceSession',
    'AttendanceRecord',
    'AcademicRecord',
    'SubjectScore',
    'Intervention',
    'Recommendation',
    'LmsActivity',
    'LearningPlan',
    'LearningTask',
    'PlacementProfile',
    'PracticeQuestion',
    'PracticeAttempt',
    'Company',
    'JobOpportunity',
    'JobApplication',
    'PlacementOffer',
    'AuditEvent',
    'CampusKnowledge',
    'EngagementRecord',
    'FeedbackRecord',
    'StudentScore',
    'SystemConfig',
    'CodingProblem',
    'StudentCodeDraft',
    'CodingSubmission',
    'StudentFile',
    'StudentFileVersion',
    'StudentWorkspaceSetting',
    'detect_language',
    'ChatConversation',
    'ChatMessage'
]


