from datetime import datetime
from backend.extensions import db
from backend.models.recommendation import Recommendation
from backend.models.academic import AcademicRecord, SubjectScore
from backend.models.attendance import AttendanceRecord
from backend.models.learning import LmsActivity
from backend.models.placement import PlacementProfile
from backend.models.audit import EngagementRecord

class RecommendationService:
    """
    Rule-based recommendation engine.
    Generates actionable, prioritized, human-centered suggestions for students and faculty advisors.
    """

    @classmethod
    def generate_student_recommendations(cls, student, save_db=True):
        """
        Evaluates student profile and generates tailored recommendations across all dimensions.
        """
        recs_to_add = []

        # 1. Attendance Check
        from backend.services.attendance_service import AttendanceService
        att = AttendanceService.calculate_student_attendance(student.student_id)
        if att['attendance_percentage'] is not None and att['attendance_percentage'] < 75.0:
            is_critical = att['attendance_percentage'] < 65.0
            recs_to_add.append({
                'title': 'Attendance Recovery & Mentor Consultation',
                'category': 'Attendance',
                'priority': 'High' if is_critical else 'Medium',
                'reason': f"Attendance is currently at {att['attendance_percentage']}% (Institutional Cutoff: 75%).",
                'trigger_data': f"Attended {att['present_count']} of {att['eligible_sessions']} eligible class sessions.",
                'suggested_action': "Meet with your faculty mentor to review lecture scheduling and sign an attendance recovery plan.",
                'responsible_role': 'Attendance Coordinator / Faculty Mentor',
                'suggested_deadline': 'Within 3 days' if is_critical else 'Within 7 days'
            })

        # 2. Academic Performance Check
        latest_academic = AcademicRecord.query.filter_by(student_id=student.student_id).order_by(AcademicRecord.semester.desc()).first()
        if latest_academic:
            if latest_academic.backlogs_count > 0:
                recs_to_add.append({
                    'title': 'Remedial Subject Coaching & Backlog Clearance',
                    'category': 'Academic',
                    'priority': 'High',
                    'reason': f"Identified {latest_academic.backlogs_count} pending backlog(s).",
                    'trigger_data': f"GPA: {latest_academic.gpa}/10.0 with {latest_academic.backlogs_count} backlog courses.",
                    'suggested_action': "Enroll in department weekend remedial classes and complete subject question bank drills.",
                    'responsible_role': 'Subject Faculty / Academic Mentor',
                    'suggested_deadline': 'Within 7 days'
                })
            elif latest_academic.gpa < 6.5:
                recs_to_add.append({
                    'title': 'Academic Mentoring & Conceptual Practice',
                    'category': 'Academic',
                    'priority': 'Medium',
                    'reason': f"Current GPA ({latest_academic.gpa}) is below the institutional benchmark of 6.5.",
                    'trigger_data': f"Semester {latest_academic.semester} GPA: {latest_academic.gpa}",
                    'suggested_action': "Join peer study circles and review previous semester exam question breakdowns.",
                    'responsible_role': 'Academic Advisor',
                    'suggested_deadline': 'Within 10 days'
                })

        # 3. LMS & Digital Learning Check
        lms_records = LmsActivity.query.filter_by(student_id=student.student_id).all()
        if lms_records:
            avg_comp = sum(r.completion_percentage for r in lms_records) / len(lms_records)
            if avg_comp < 60.0:
                recs_to_add.append({
                    'title': 'Digital Learning Milestone Catch-Up',
                    'category': 'Learning',
                    'priority': 'Medium',
                    'reason': f"LMS course module completion is at {round(avg_comp, 1)}%.",
                    'trigger_data': f"Online modules completed: {round(avg_comp, 1)}% across enrolled subjects.",
                    'suggested_action': "Follow a structured 30-minute daily learning block to finish pending quizzes and laboratory modules.",
                    'responsible_role': 'Course Instructor',
                    'suggested_deadline': 'Within 5 days'
                })

        # 4. Placement & Skill Gap Check
        placement = PlacementProfile.query.filter_by(student_id=student.student_id).first()
        if placement:
            if placement.coding_score < 60.0:
                recs_to_add.append({
                    'title': 'Data Structures & Algorithmic Practice',
                    'category': 'Skills',
                    'priority': 'High' if placement.coding_score < 45.0 else 'Medium',
                    'reason': f"Coding assessment benchmark ({placement.coding_score}%) indicates scope for practice.",
                    'trigger_data': f"Current coding benchmark score: {placement.coding_score}% for target role '{placement.target_role}'.",
                    'suggested_action': "Solve 3 medium-difficulty algorithmic practice questions per week in the Coding Lab.",
                    'responsible_role': 'Coding Lab Instructor',
                    'suggested_deadline': 'Within 14 days'
                })

            if placement.aptitude_score < 60.0:
                recs_to_add.append({
                    'title': 'Quantitative & Logical Aptitude Training',
                    'category': 'Skills',
                    'priority': 'Medium',
                    'reason': f"Aptitude score ({placement.aptitude_score}%) requires focused practice.",
                    'trigger_data': f"Aptitude benchmark score: {placement.aptitude_score}%",
                    'suggested_action': "Complete weekly online aptitude mock tests covering quantitative reasoning and data interpretation.",
                    'responsible_role': 'Placement Aptitude Trainer',
                    'suggested_deadline': 'Within 14 days'
                })

            if placement.communication_score < 65.0:
                recs_to_add.append({
                    'title': 'Communication & Mock Interview Drill',
                    'category': 'Placement',
                    'priority': 'Medium',
                    'reason': f"Communication preparedness index ({placement.communication_score}%) requires strengthening.",
                    'trigger_data': f"Communication assessment: {placement.communication_score}%",
                    'suggested_action': "Participate in bi-weekly mock HR and technical interview exercises.",
                    'responsible_role': 'Career Counselor / Placement Officer',
                    'suggested_deadline': 'Within 10 days'
                })

            if placement.readiness_percentage < 55.0 and student.academic_year >= 3:
                recs_to_add.append({
                    'title': 'Placement Readiness Acceleration Program',
                    'category': 'Placement',
                    'priority': 'High',
                    'reason': f"Overall placement readiness is {placement.readiness_percentage}% in Academic Year {student.academic_year}.",
                    'trigger_data': f"Readiness: {placement.readiness_percentage}% (Target: 75%+).",
                    'suggested_action': "Schedule a 1-on-1 career mapping review with the institutional Placement Officer.",
                    'responsible_role': 'Placement Officer',
                    'suggested_deadline': 'Within 7 days'
                })

        # 5. Engagement Check
        eng_count = EngagementRecord.query.filter_by(student_id=student.student_id).count()
        if eng_count == 0:
            recs_to_add.append({
                'title': 'Co-Curricular & Skill Workshop Engagement',
                'category': 'Engagement',
                'priority': 'Low',
                'reason': "No active participation recorded in hackathons, student clubs, or technical seminars.",
                'trigger_data': "0 co-curricular engagement records found.",
                'suggested_action': "Join at least one recognized student chapter or enroll in an upcoming campus hackathon.",
                'responsible_role': 'Student Activities Coordinator',
                'suggested_deadline': 'Within 21 days'
            })

        # Fallback positive reinforcement if performing excellently
        if not recs_to_add:
            recs_to_add.append({
                'title': 'Honors & Competitive Innovation Track',
                'category': 'Career',
                'priority': 'Low',
                'reason': "Demonstrating strong performance across academic, attendance, and placement metrics.",
                'trigger_data': "High overall composite score and consistent attendance.",
                'suggested_action': "Consider submitting research papers, applying for tier-1 hackathons, or pursuing industry cloud certifications.",
                'responsible_role': 'Faculty Mentor / Research Guide',
                'suggested_deadline': 'Within 30 days'
            })

        if save_db:
            existing_recs = Recommendation.query.filter_by(student_id=student.student_id).all()
            existing_titles = {r.title for r in existing_recs}
            for item in recs_to_add:
                if item['title'] not in existing_titles:
                    rec = Recommendation(
                        student_id=student.student_id,
                        title=item['title'],
                        category=item['category'],
                        priority=item['priority'],
                        reason=item['reason'],
                        trigger_data=item['trigger_data'],
                        suggested_action=item['suggested_action'],
                        responsible_role=item.get('responsible_role', 'Faculty Mentor'),
                        suggested_deadline=item.get('suggested_deadline', 'Within 7 days'),
                        status='Active'
                    )
                    db.session.add(rec)
            db.session.commit()

        return recs_to_add

    @classmethod
    def update_recommendation_status(cls, recommendation_id, new_status):
        """
        Updates recommendation follow-up status (e.g., Active, In Progress, Completed, Dismissed).
        """
        valid_statuses = {'Active', 'Pending', 'In Progress', 'Completed', 'Dismissed'}
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Valid options: {valid_statuses}")

        rec = Recommendation.query.get(recommendation_id)
        if not rec:
            return None

        rec.status = new_status
        db.session.commit()
        return rec
