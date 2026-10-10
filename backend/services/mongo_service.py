import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.db_mongo import get_mongo_db, get_mongo_collection, mongo_manager
from backend.models.mongo_models import (
    MongoStudentSchema, MongoAcademicSchema, MongoAttendanceSchema,
    MongoSkillsLearningSchema, MongoFeedbackSchema, MongoRecommendationSchema
)
from backend.models.student import Student
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceRecord
from backend.models.learning import LmsActivity, LearningPlan
from backend.models.placement import PlacementProfile
from backend.models.audit import FeedbackRecord, StudentScore
from backend.models.recommendation import Recommendation
from backend.services.attendance_service import AttendanceService
from backend.services.success_score import SuccessScoreService

logger = logging.getLogger('smart_campus.mongo_service')

class MongoStudentService:
    """
    CRUD and synchronization service for MongoDB Atlas collections.
    """

    @classmethod
    def is_connected(cls) -> bool:
        db = get_mongo_db()
        return db is not None

    @classmethod
    def get_unified_student_document(cls, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an integrated student record from MongoDB Atlas collections.
        """
        db = get_mongo_db()
        if db is None:
            return None

        stu_id = str(student_id).strip().upper()
        student_doc = db.students.find_one({'student_id': stu_id}, {'_id': 0})
        if not student_doc:
            return None

        # Fetch associated collection documents
        academic_recs = list(db.academic_records.find({'student_id': stu_id}, {'_id': 0}))
        attendance_recs = list(db.attendance_records.find({'student_id': stu_id}, {'_id': 0}).limit(50))
        skills_doc = db.skills_learning.find_one({'student_id': stu_id}, {'_id': 0})
        feedbacks = list(db.student_feedbacks.find({'student_id': stu_id}, {'_id': 0}))
        recommendations = list(db.ai_recommendations.find({'student_id': stu_id}, {'_id': 0}))

        student_doc['academic_records'] = academic_recs
        student_doc['attendance_records'] = attendance_recs
        student_doc['skills_learning'] = skills_doc or {}
        student_doc['feedback_records'] = feedbacks
        student_doc['recommendations'] = recommendations
        student_doc['source'] = 'MongoDB Atlas'

        return student_doc

    @classmethod
    def list_students(cls, filter_params: Optional[Dict[str, Any]] = None, page: int = 1, per_page: int = 15) -> Dict[str, Any]:
        """
        Queries student profiles from MongoDB Atlas with pagination and filters.
        """
        db = get_mongo_db()
        if db is None:
            return {'items': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0}

        query = {}
        filter_params = filter_params or {}

        if filter_params.get('department'):
            query['department'] = filter_params['department']
        if filter_params.get('academic_year'):
            query['academic_year'] = int(filter_params['academic_year'])
        if filter_params.get('semester'):
            query['semester'] = int(filter_params['semester'])
        if filter_params.get('status'):
            query['status'] = filter_params['status']
        if filter_params.get('search'):
            s = filter_params['search'].strip()
            query['$or'] = [
                {'student_id': {'$regex': s, '$options': 'i'}},
                {'first_name': {'$regex': s, '$options': 'i'}},
                {'last_name': {'$regex': s, '$options': 'i'}},
                {'email': {'$regex': s, '$options': 'i'}}
            ]

        total = db.students.count_documents(query)
        skip = (page - 1) * per_page
        cursor = db.students.find(query, {'_id': 0}).sort('student_id', 1).skip(skip).limit(per_page)
        items = list(cursor)

        import math
        pages = math.ceil(total / per_page) if per_page > 0 else 1

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        }

    @classmethod
    def create_or_update_student(cls, data: Dict[str, Any]) -> (bool, Optional[str], Optional[Dict[str, Any]]):
        """
        Creates or updates a student profile document in MongoDB Atlas.
        """
        db = get_mongo_db()
        if db is None:
            return False, "MongoDB is not connected", None

        is_valid, err = MongoStudentSchema.validate(data)
        if not is_valid:
            return False, err, None

        doc = MongoStudentSchema.format_document(data)
        stu_id = doc['student_id']

        db.students.update_one(
            {'student_id': stu_id},
            {'$set': doc},
            upsert=True
        )

        return True, None, doc

    @classmethod
    def delete_student(cls, student_id: str) -> (bool, Optional[str]):
        """
        Cascades deletion of a student and related sub-collections across MongoDB Atlas.
        """
        db = get_mongo_db()
        if db is None:
            return False, "MongoDB is not connected"

        stu_id = str(student_id).strip().upper()
        res = db.students.delete_one({'student_id': stu_id})
        db.academic_records.delete_many({'student_id': stu_id})
        db.attendance_records.delete_many({'student_id': stu_id})
        db.skills_learning.delete_many({'student_id': stu_id})
        db.student_feedbacks.delete_many({'student_id': stu_id})
        db.ai_recommendations.delete_many({'student_id': stu_id})

        return (res.deleted_count > 0), None

    @classmethod
    def sync_student_to_mongo(cls, student: Student) -> bool:
        """
        Exports a complete SQLite Student graph into MongoDB Atlas collections.
        """
        db = get_mongo_db()
        if db is None or not student:
            return False

        stu_id = student.student_id

        # 1. Upsert Student Profile
        stu_dict = student.to_dict()
        cls.create_or_update_student(stu_dict)

        # 2. Upsert Academic Records
        db.academic_records.delete_many({'student_id': stu_id})
        for rec in student.academic_records:
            subj_scores = [s.to_dict() for s in SubjectScore.query.filter_by(student_id=stu_id, semester=rec.semester).all()]
            ac_data = rec.to_dict()
            ac_data['subject_scores'] = subj_scores
            db.academic_records.insert_one(MongoAcademicSchema.format_document(ac_data))

        # 3. Upsert Attendance Records
        db.attendance_records.delete_many({'student_id': stu_id})
        att_recs = AttendanceRecord.query.filter_by(student_id=stu_id).limit(100).all()
        for att in att_recs:
            session_subj = att.session.subject if att.session else 'General'
            session_date = att.session.session_date.isoformat() if att.session and att.session.session_date else None
            db.attendance_records.insert_one(MongoAttendanceSchema.format_document({
                'student_id': stu_id,
                'session_id': att.session_id,
                'subject': session_subj,
                'status': att.status,
                'remarks': att.remarks,
                'session_date': session_date
            }))

        # 4. Upsert Skills & Learning Profile
        placement = PlacementProfile.query.filter_by(student_id=stu_id).first()
        lms_list = [l.to_dict() for l in LmsActivity.query.filter_by(student_id=stu_id).all()]
        plans_list = [p.to_dict() for p in LearningPlan.query.filter_by(student_id=stu_id).all()]
        skills_data = {
            'student_id': stu_id,
            'target_role': placement.target_role if placement else 'Software Developer',
            'technical_skills': placement.to_dict().get('skills_list', []) if placement else ['Python', 'SQL'],
            'aptitude_score': placement.aptitude_score if placement else 0.0,
            'coding_score': placement.coding_score if placement else 0.0,
            'interview_score': placement.interview_score if placement else 0.0,
            'readiness_percentage': placement.readiness_percentage if placement else 0.0,
            'learning_plans': plans_list,
            'lms_courses': lms_list
        }
        db.skills_learning.update_one(
            {'student_id': stu_id},
            {'$set': MongoSkillsLearningSchema.format_document(skills_data)},
            upsert=True
        )

        # 5. Upsert Student Feedbacks
        db.student_feedbacks.delete_many({'student_id': stu_id})
        for fb in FeedbackRecord.query.filter_by(student_id=stu_id).all():
            db.student_feedbacks.insert_one(MongoFeedbackSchema.format_document({
                'student_id': stu_id,
                'faculty_id': fb.faculty_id,
                'term': fb.term,
                'behavioral_score': fb.behavioral_score,
                'punctuality_score': fb.punctuality_score,
                'teamwork_score': fb.teamwork_score,
                'initiative_score': fb.initiative_score,
                'general_notes': fb.general_notes
            }))

        # 6. Upsert AI Recommendations
        db.ai_recommendations.delete_many({'student_id': stu_id})
        for rec in Recommendation.query.filter_by(student_id=stu_id).all():
            db.ai_recommendations.insert_one(MongoRecommendationSchema.format_document({
                'student_id': stu_id,
                'title': rec.title,
                'category': rec.category,
                'priority': rec.priority,
                'reason': rec.reason,
                'suggested_action': rec.suggested_action,
                'responsible_role': rec.responsible_role,
                'suggested_deadline': rec.suggested_deadline,
                'status': rec.status
            }))

        return True

    @classmethod
    def sync_all_database_to_mongo(cls) -> Dict[str, Any]:
        """
        Synchronizes all students from relational database to MongoDB Atlas.
        """
        db = get_mongo_db()
        if db is None:
            return {'success': False, 'message': 'MongoDB Atlas is not connected', 'count': 0}

        students = Student.query.all()
        synced_count = 0
        for stu in students:
            try:
                if cls.sync_student_to_mongo(stu):
                    synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing student {stu.student_id} to Mongo: {e}")

        status = mongo_manager.get_status()
        return {
            'success': True,
            'message': f"Synchronized {synced_count} student profiles and sub-documents to MongoDB Atlas.",
            'count': synced_count,
            'atlas_status': status
        }
