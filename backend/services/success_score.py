import json
from backend.config import Config
from backend.extensions import db
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceRecord, AttendanceSession
from backend.models.learning import LmsActivity
from backend.models.placement import PlacementProfile
from backend.models.audit import EngagementRecord, FeedbackRecord, StudentScore, SystemConfig

class SuccessScoreService:
    """
    Configurable Student Success Scoring Service.
    Computes a transparent composite score (0-100) based on weighted institutional indicators.
    """

    DEFAULT_WEIGHTS = {
        'academic': 0.30,
        'attendance': 0.20,
        'lms': 0.10,
        'engagement': 0.10,
        'placement': 0.15,
        'skills': 0.10,
        'feedback': 0.05
    }

    @classmethod
    def get_weights(cls):
        """Fetches active weights from SystemConfig or fallback to Config/defaults."""
        try:
            cfg = SystemConfig.query.filter_by(config_key='scoring_weights').first()
            if cfg and cfg.config_value:
                weights = json.loads(cfg.config_value)
                if cls.validate_weights(weights):
                    return weights
        except Exception:
            pass
        return getattr(Config, 'WEIGHTS', cls.DEFAULT_WEIGHTS)

    @classmethod
    def validate_weights(cls, weights):
        """Validates that weights sum to 1.0 within floating point tolerance."""
        if not isinstance(weights, dict):
            return False
        required_keys = {'academic', 'attendance', 'lms', 'engagement', 'placement', 'skills', 'feedback'}
        if not required_keys.issubset(weights.keys()):
            return False
        total = sum(float(v) for v in weights.values())
        return abs(total - 1.0) < 0.001 or abs(total - 100.0) < 0.1

    @classmethod
    def normalize_academic(cls, student):
        """
        Normalizes academic standing:
        GPA on 10-point scale -> 10 * 10 = 100.
        Penalizes for active backlogs (e.g., -10 per backlog, min 0).
        """
        latest_rec = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.desc()).first()
        if not latest_rec:
            # Check subject scores
            scores = SubjectScore.query.filter_by(student_id=student.student_id).all()
            if scores:
                avg_pct = sum((s.marks_obtained / s.max_marks * 100) for s in scores) / len(scores)
                return max(0.0, min(100.0, avg_pct))
            return 70.0 # Institutional benchmark fallback for new enrollments

        gpa_norm = (latest_rec.gpa / 10.0) * 100.0 if latest_rec.gpa <= 10.0 else latest_rec.gpa
        backlog_penalty = latest_rec.backlogs_count * 10.0
        return max(0.0, min(100.0, gpa_norm - backlog_penalty))

    @classmethod
    def normalize_attendance(cls, student):
        """
        Normalizes attendance percentage based on institutional policy.
        """
        from backend.services.attendance_service import AttendanceService
        stats = AttendanceService.calculate_student_attendance(student.student_id)
        if stats['attendance_percentage'] is not None:
            return float(stats['attendance_percentage'])
        return 75.0 # Benchmark fallback if no sessions recorded yet

    @classmethod
    def normalize_lms(cls, student):
        """
        Normalizes LMS platform engagement: module completion rate + quiz average.
        """
        activities = LmsActivity.query.filter_by(student_id=student.student_id).all()
        if not activities:
            return 65.0
        
        comp_rates = [a.completion_percentage for a in activities]
        quiz_scores = [a.quiz_score_avg for a in activities]
        
        avg_comp = sum(comp_rates) / len(comp_rates) if comp_rates else 0
        avg_quiz = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        
        lms_score = (avg_comp * 0.5) + (avg_quiz * 0.5)
        return max(0.0, min(100.0, lms_score))

    @classmethod
    def normalize_engagement(cls, student):
        """
        Normalizes extracurricular / co-curricular engagement.
        """
        records = EngagementRecord.query.filter_by(student_id=student.student_id).all()
        if not records:
            return 60.0
        total_points = sum(r.score_points for r in records)
        # 50 points or above maps to 100%
        score = min(100.0, (total_points / 50.0) * 100.0)
        return max(0.0, score)

    @classmethod
    def normalize_placement(cls, student):
        """
        Normalizes placement readiness score.
        """
        prof = PlacementProfile.query.filter_by(student_id=student.student_id).first()
        if not prof:
            return 60.0
        return prof.calculate_readiness()

    @classmethod
    def normalize_skills(cls, student):
        """
        Normalizes technical & soft skills assessments.
        """
        prof = PlacementProfile.query.filter_by(student_id=student.student_id).first()
        if not prof:
            return 65.0
        skill_score = (prof.coding_score * 0.6) + (prof.aptitude_score * 0.4)
        return max(0.0, min(100.0, skill_score))

    @classmethod
    def normalize_feedback(cls, student):
        """
        Normalizes faculty behavioral and support feedback scores.
        """
        feedbacks = FeedbackRecord.query.filter_by(student_id=student.student_id).all()
        if not feedbacks:
            return 75.0
        avg = sum(f.average_score for f in feedbacks) / len(feedbacks)
        return max(0.0, min(100.0, avg))

    @classmethod
    def calculate_student_score(cls, student, save_db=True):
        """
        Calculates the complete composite success score for a student.
        Returns a dictionary with raw components, weights, and final composite score.
        """
        weights = cls.get_weights()
        
        # Ensure weights sum to 1.0
        w_total = sum(weights.values())
        norm_weights = {k: v / w_total for k, v in weights.items()}

        academic = cls.normalize_academic(student)
        attendance = cls.normalize_attendance(student)
        lms = cls.normalize_lms(student)
        engagement = cls.normalize_engagement(student)
        placement = cls.normalize_placement(student)
        skills = cls.normalize_skills(student)
        feedback = cls.normalize_feedback(student)

        composite = (
            (academic * norm_weights['academic']) +
            (attendance * norm_weights['attendance']) +
            (lms * norm_weights['lms']) +
            (engagement * norm_weights['engagement']) +
            (placement * norm_weights['placement']) +
            (skills * norm_weights['skills']) +
            (feedback * norm_weights['feedback'])
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        # Status Label & Color Mapping
        if composite >= 80.0:
            status_label = 'High Performing'
            status_color = '#10b981'
            status_badge = 'success'
            status_desc = 'Student demonstrates excellent holistic engagement across academic, attendance, and placement dimensions.'
        elif composite >= 65.0:
            status_label = 'Good Standing'
            status_color = '#2563eb'
            status_badge = 'primary'
            status_desc = 'Student is on track with steady academic progress and satisfactory institutional compliance.'
        elif composite >= 50.0:
            status_label = 'Moderate Risk'
            status_color = '#f59e0b'
            status_badge = 'warning'
            status_desc = 'Student shows vulnerability in specific indicators; targeted mentoring is recommended.'
        else:
            status_label = 'Critical Risk'
            status_color = '#ef4444'
            status_badge = 'danger'
            status_desc = 'Student requires immediate faculty intervention across multiple risk dimensions.'

        # Detailed indicator contributions & explainability
        indicators = [
            {
                'key': 'academic',
                'name': 'Academic Standing',
                'raw_score': round(academic, 1),
                'weight': norm_weights['academic'],
                'weight_pct': f"{int(round(norm_weights['academic'] * 100))}%",
                'weighted_contribution': round(academic * norm_weights['academic'], 1),
                'status': 'Strong' if academic >= 75 else ('Satisfactory' if academic >= 60 else 'Needs Attention'),
                'description': 'Normalized GPA & backlog deductions'
            },
            {
                'key': 'attendance',
                'name': 'Attendance Compliance',
                'raw_score': round(attendance, 1),
                'weight': norm_weights['attendance'],
                'weight_pct': f"{int(round(norm_weights['attendance'] * 100))}%",
                'weighted_contribution': round(attendance * norm_weights['attendance'], 1),
                'status': 'Strong' if attendance >= 75 else ('Warning' if attendance >= 65 else 'Critical'),
                'description': 'Institutional class lecture attendance percentage'
            },
            {
                'key': 'placement',
                'name': 'Placement Readiness',
                'raw_score': round(placement, 1),
                'weight': norm_weights['placement'],
                'weight_pct': f"{int(round(norm_weights['placement'] * 100))}%",
                'weighted_contribution': round(placement * norm_weights['placement'], 1),
                'status': 'Strong' if placement >= 70 else ('Satisfactory' if placement >= 50 else 'Needs Attention'),
                'description': 'Composite career readiness & mock drill benchmark'
            },
            {
                'key': 'skills',
                'name': 'Technical & Soft Skills',
                'raw_score': round(skills, 1),
                'weight': norm_weights['skills'],
                'weight_pct': f"{int(round(norm_weights['skills'] * 100))}%",
                'weighted_contribution': round(skills * norm_weights['skills'], 1),
                'status': 'Strong' if skills >= 70 else ('Satisfactory' if skills >= 50 else 'Needs Attention'),
                'description': 'Coding proficiency (60%) & aptitude assessment (40%)'
            },
            {
                'key': 'lms',
                'name': 'LMS & Digital Learning',
                'raw_score': round(lms, 1),
                'weight': norm_weights['lms'],
                'weight_pct': f"{int(round(norm_weights['lms'] * 100))}%",
                'weighted_contribution': round(lms * norm_weights['lms'], 1),
                'status': 'Strong' if lms >= 70 else ('Satisfactory' if lms >= 50 else 'Needs Attention'),
                'description': 'Digital course module completion and quiz mastery'
            },
            {
                'key': 'engagement',
                'name': 'Campus Engagement',
                'raw_score': round(engagement, 1),
                'weight': norm_weights['engagement'],
                'weight_pct': f"{int(round(norm_weights['engagement'] * 100))}%",
                'weighted_contribution': round(engagement * norm_weights['engagement'], 1),
                'status': 'Strong' if engagement >= 70 else ('Satisfactory' if engagement >= 50 else 'Needs Attention'),
                'description': 'Co-curricular, hackathons, and certified workshops'
            },
            {
                'key': 'feedback',
                'name': 'Faculty & Peer Feedback',
                'raw_score': round(feedback, 1),
                'weight': norm_weights['feedback'],
                'weight_pct': f"{int(round(norm_weights['feedback'] * 100))}%",
                'weighted_contribution': round(feedback * norm_weights['feedback'], 1),
                'status': 'Strong' if feedback >= 70 else ('Satisfactory' if feedback >= 60 else 'Needs Attention'),
                'description': 'Faculty behavioral, advisory, and collaborative feedback'
            }
        ]

        # Identify positive contributors and improvement areas
        positive_contributors = [
            ind for ind in sorted(indicators, key=lambda x: x['raw_score'], reverse=True)
            if ind['raw_score'] >= 70.0
        ]
        improvement_areas = [
            ind for ind in sorted(indicators, key=lambda x: x['raw_score'])
            if ind['raw_score'] < 70.0
        ]

        # Classify risk level
        from backend.services.risk_analysis import RiskAnalysisService
        risk_data = RiskAnalysisService.evaluate_risk(
            student_id=student.student_id,
            success_score=composite,
            academic_score=academic,
            attendance_score=attendance,
            lms_score=lms,
            placement_score=placement
        )

        explainability = {
            'methodology': 'Weighted Normalized Multi-Dimensional Composite Scoring',
            'formula_description': 'Success Score = Sum(Indicator_Normalized_Score * Configurable_Weight)',
            'disclaimer': 'Success scores represent historical institutional indicators for academic advising and do not guarantee future performance.',
            'positive_contributors_count': len(positive_contributors),
            'improvement_areas_count': len(improvement_areas)
        }

        score_data = {
            'student_id': student.student_id,
            'score': composite,
            'success_score': composite,
            'category': status_label,
            'status_label': status_label,
            'status_color': status_color,
            'status_badge': status_badge,
            'status_description': status_desc,
            'academic_component': round(academic, 1),
            'attendance_component': round(attendance, 1),
            'lms_component': round(lms, 1),
            'engagement_component': round(engagement, 1),
            'placement_component': round(placement, 1),
            'skills_component': round(skills, 1),
            'feedback_component': round(feedback, 1),
            'indicators': indicators,
            'positive_contributors': positive_contributors,
            'improvement_areas': improvement_areas,
            'explainability': explainability,
            'risk_level': risk_data['risk_level'],
            'risk_factors': risk_data['risk_factors'],
            'needs_immediate_attention': risk_data.get('needs_immediate_attention', False),
            'weights_applied': norm_weights
        }

        if save_db:
            score_rec = StudentScore.query.filter_by(student_id=student.student_id).first()
            if not score_rec:
                score_rec = StudentScore(student_id=student.student_id)
                db.session.add(score_rec)
            
            score_rec.academic_component = academic
            score_rec.attendance_component = attendance
            score_rec.lms_component = lms
            score_rec.engagement_component = engagement
            score_rec.placement_component = placement
            score_rec.skills_component = skills
            score_rec.feedback_component = feedback
            score_rec.success_score = composite
            score_rec.risk_level = risk_data['risk_level']
            score_rec.risk_factors_json = json.dumps(risk_data['risk_factors'])
            
            db.session.commit()

        return score_data

    @classmethod
    def recalculate_all_scores(cls):
        """Recalculates scores for all students across the institution."""
        from backend.models.student import Student
        students = Student.query.all()
        results = []
        for stu in students:
            res = cls.calculate_student_score(stu, save_db=True)
            results.append(res)
        return results
