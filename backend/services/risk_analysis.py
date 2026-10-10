from backend.config import Config
from backend.extensions import db
from backend.models.audit import SystemConfig

class RiskAnalysisService:
    """
    Explainable, rule-based Academic Risk Analysis service.
    Classifies student risk and details precise contributing triggers and human-centered support actions.
    """

    @classmethod
    def get_thresholds(cls):
        high = Config.RISK_HIGH_THRESHOLD
        med = Config.RISK_MEDIUM_THRESHOLD
        try:
            cfg_h = SystemConfig.query.filter_by(config_key='risk_high_threshold').first()
            if cfg_h:
                high = float(cfg_h.config_value)
            cfg_m = SystemConfig.query.filter_by(config_key='risk_medium_threshold').first()
            if cfg_m:
                med = float(cfg_m.config_value)
        except Exception:
            pass
        return {'high': high, 'medium': med}

    @classmethod
    def evaluate_risk(cls, student_id, success_score, academic_score=None, attendance_score=None, lms_score=None, placement_score=None, academic_year=1):
        """
        Evaluates risk category, academic risk, placement outcome risk, and generates transparent triggers & evidence.
        """
        thresholds = cls.get_thresholds()
        risk_factors = []

        # 1. Overall composite risk
        if success_score < thresholds['high']:
            risk_level = 'High'
            risk_factors.append({
                'dimension': 'Composite Success Score',
                'severity': 'Critical',
                'score': success_score,
                'evidence': f"Overall success score is {success_score}/100, which falls below the high-risk threshold ({thresholds['high']}).",
                'suggested_action': "Initiate comprehensive multi-disciplinary advisory review and mentoring."
            })
        elif success_score < thresholds['medium']:
            risk_level = 'Medium'
            risk_factors.append({
                'dimension': 'Composite Success Score',
                'severity': 'Moderate',
                'score': success_score,
                'evidence': f"Overall success score is {success_score}/100, indicating room for targeted support.",
                'suggested_action': "Encourage participation in peer tutoring and focused skill labs."
            })
        else:
            risk_level = 'Low'

        # 2. Specific Domain Risk Triggers
        # Attendance Risk
        if attendance_score is not None and attendance_score < 75.0:
            severity = 'Critical' if attendance_score < 65.0 else 'Warning'
            if risk_level == 'Low':
                risk_level = 'Medium'
            risk_factors.append({
                'dimension': 'Attendance',
                'severity': severity,
                'score': attendance_score,
                'evidence': f"Current attendance is {attendance_score}%, which is below the mandatory 75% institutional cutoff.",
                'suggested_action': "Issue attendance advisory notice and conduct counselor check-in."
            })

        # Academic Performance Risk
        academic_risk = 'Low'
        if academic_score is not None:
            if academic_score < 50.0:
                academic_risk = 'High'
                if risk_level == 'Low':
                    risk_level = 'Medium'
                risk_factors.append({
                    'dimension': 'Academic Standing',
                    'severity': 'Critical',
                    'score': academic_score,
                    'evidence': f"Academic performance indicator is {academic_score}/100, reflecting severe subject struggles or active backlogs.",
                    'suggested_action': "Assign mandatory remedial subject coaching and weekly progress milestones."
                })
            elif academic_score < 60.0:
                academic_risk = 'Medium'
                if risk_level == 'Low':
                    risk_level = 'Medium'
                risk_factors.append({
                    'dimension': 'Academic Standing',
                    'severity': 'Warning',
                    'score': academic_score,
                    'evidence': f"Academic performance indicator is {academic_score}/100, below standard benchmark.",
                    'suggested_action': "Assign peer tutor and schedule faculty office hours review."
                })

        # LMS Digital Engagement Risk
        if lms_score is not None and lms_score < 50.0:
            risk_factors.append({
                'dimension': 'LMS Activity',
                'severity': 'Warning',
                'score': lms_score,
                'evidence': f"Online learning module completion and quiz performance is low ({lms_score}/100).",
                'suggested_action': "Provide structured weekly study plan with bite-sized learning milestones."
            })

        # Placement Outcome Risk
        placement_risk = 'Low'
        if placement_score is not None:
            if placement_score < 45.0:
                placement_risk = 'High'
                risk_factors.append({
                    'dimension': 'Placement Readiness',
                    'severity': 'Critical' if academic_year >= 3 else 'Warning',
                    'score': placement_score,
                    'evidence': f"Placement readiness index is {placement_score}/100 indicating significant skill and mock assessment deficits.",
                    'suggested_action': "Enroll in fast-track placement readiness bootcamp and 1-on-1 career mapping."
                })
            elif placement_score < 60.0:
                placement_risk = 'Medium'
                risk_factors.append({
                    'dimension': 'Placement Readiness',
                    'severity': 'Warning',
                    'score': placement_score,
                    'evidence': f"Placement readiness index is {placement_score}/100 with technical or aptitude practice gaps.",
                    'suggested_action': "Recommend role-specific aptitude practice and coding assessment mock drills."
                })

        # Immediate Faculty Attention Flag
        critical_count = sum(1 for f in risk_factors if f.get('severity') == 'Critical')
        needs_immediate_attention = (
            risk_level == 'High' or
            critical_count >= 2 or
            (attendance_score is not None and attendance_score < 60.0) or
            (academic_score is not None and academic_score < 45.0)
        )

        return {
            'student_id': student_id,
            'risk_level': risk_level,
            'academic_risk': academic_risk,
            'placement_risk': placement_risk,
            'risk_score': success_score,
            'success_score': success_score,
            'needs_immediate_attention': needs_immediate_attention,
            'risk_factors': risk_factors,
            'factor_count': len(risk_factors),
            'critical_factor_count': critical_count
        }

    @classmethod
    def evaluate_student_risk(cls, student):
        """
        Evaluates risk for a given Student model instance or student_id.
        """
        from backend.models.student import Student
        from backend.models.audit import StudentScore
        from backend.services.attendance_service import AttendanceService
        from backend.models.academic import AcademicRecord

        if isinstance(student, str):
            student = Student.query.filter_by(student_id=student).first()
            if not student:
                return {
                    'risk_level': 'Low',
                    'academic_risk': 'Low',
                    'placement_risk': 'Low',
                    'success_score': 75.0,
                    'needs_immediate_attention': False,
                    'risk_factors': [],
                    'factor_count': 0
                }

        score_rec = StudentScore.query.filter_by(student_id=student.student_id).first()
        att_data = AttendanceService.calculate_student_attendance(student.student_id)
        att_score = att_data.get('attendance_percentage') or att_data.get('percentage')

        acad_rec = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.desc()).first()
        acad_score = (acad_rec.gpa * 10.0) if acad_rec and acad_rec.gpa else None

        if score_rec and score_rec.success_score is not None:
            success_score = score_rec.success_score
        else:
            success_score = (att_score if att_score is not None else 75.0) * 0.5 + (acad_score if acad_score is not None else 70.0) * 0.5

        return cls.evaluate_risk(
            student_id=student.student_id,
            success_score=success_score,
            academic_score=acad_score,
            attendance_score=att_score,
            lms_score=score_rec.lms_component if score_rec else None,
            placement_score=score_rec.placement_component if score_rec else None,
            academic_year=student.academic_year
        )

    @classmethod
    def get_at_risk_students(cls, department=None, risk_level=None, search=None, immediate_only=False, limit=200):
        """
        Returns enriched list of at-risk students with filtering and search support.
        """
        from backend.models.audit import StudentScore
        from backend.models.student import Student
        from backend.models.academic import AcademicRecord
        import json

        query = db.session.query(StudentScore, Student).join(Student, StudentScore.student_id == Student.student_id)

        if department:
            query = query.filter(Student.department == department)
        if risk_level:
            query = query.filter(StudentScore.risk_level == risk_level)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Student.student_id.ilike(search_term)) |
                (Student.first_name.ilike(search_term)) |
                (Student.last_name.ilike(search_term)) |
                (Student.department.ilike(search_term))
            )

        results = query.order_by(StudentScore.success_score.asc()).limit(limit).all()

        at_risk_list = []
        for score, student in results:
            factors = []
            if score.risk_factors_json:
                try:
                    factors = json.loads(score.risk_factors_json)
                except Exception:
                    factors = []

            critical_count = sum(1 for f in factors if f.get('severity') == 'Critical')
            needs_immediate = (
                score.risk_level == 'High' or
                critical_count >= 2 or
                score.attendance_component < 60.0 or
                score.academic_component < 45.0
            )

            if immediate_only and not needs_immediate:
                continue

            acad_rec = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.desc()).first()

            reasons_summary = [f.get('dimension', '') + ": " + f.get('evidence', '') for f in factors[:3]]

            at_risk_list.append({
                'student_id': student.student_id,
                'student_name': student.full_name,
                'email': student.email,
                'department': student.department,
                'academic_year': student.academic_year,
                'semester': student.semester,
                'gpa': acad_rec.gpa if acad_rec else round(score.academic_component / 10.0, 2),
                'backlogs': acad_rec.backlogs_count if acad_rec else 0,
                'success_score': round(score.success_score, 1),
                'risk_level': score.risk_level,
                'attendance_score': round(score.attendance_component, 1),
                'academic_score': round(score.academic_component, 1),
                'placement_score': round(score.placement_component, 1),
                'lms_score': round(score.lms_component, 1),
                'needs_immediate_attention': needs_immediate,
                'critical_factor_count': critical_count,
                'risk_factors': factors,
                'reasons_summary': reasons_summary
            })

        return at_risk_list

    @classmethod
    def get_institutional_risk_summary(cls):
        """Returns risk distribution counts and departmental hotspots."""
        from backend.models.audit import StudentScore
        from backend.models.student import Student

        scores = db.session.query(StudentScore, Student).join(Student, StudentScore.student_id == Student.student_id).all()
        
        high_count = 0
        med_count = 0
        low_count = 0
        immediate_count = 0
        dept_risk = {}

        for score, student in scores:
            level = score.risk_level or 'Low'
            if level == 'High':
                high_count += 1
            elif level == 'Medium':
                med_count += 1
            else:
                low_count += 1

            if score.success_score < 50.0 or score.attendance_component < 60.0 or score.academic_component < 45.0:
                immediate_count += 1

            dept = student.department
            if dept not in dept_risk:
                dept_risk[dept] = {'High': 0, 'Medium': 0, 'Low': 0, 'total': 0}
            dept_risk[dept][level] = dept_risk[dept].get(level, 0) + 1
            dept_risk[dept]['total'] += 1

        total = len(scores)
        return {
            'total_students_assessed': total,
            'high_risk_count': high_count,
            'medium_risk_count': med_count,
            'low_risk_count': low_count,
            'needs_immediate_attention_count': immediate_count,
            'high_risk_percentage': round((high_count / total * 100), 1) if total else 0,
            'medium_risk_percentage': round((med_count / total * 100), 1) if total else 0,
            'low_risk_percentage': round((low_count / total * 100), 1) if total else 0,
            'department_risk_breakdown': dept_risk
        }
