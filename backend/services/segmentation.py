from backend.extensions import db
from backend.models.student import Student
from backend.models.audit import StudentScore
from backend.models.academic import AcademicRecord
from backend.models.placement import PlacementProfile

class StudentSegmentationService:
    """
    Transparent, rule-based Student Segmentation Service.
    Groups students into meaningful, actionable institutional cohorts based on multi-indicator performance.
    """

    SEGMENT_DEFINITIONS = [
        {
            'id': 'academic_achievers_placement_gap',
            'name': 'Academic Achievers with Placement Gaps',
            'short_name': 'Academic Star / Placement Gap',
            'badge_color': '#3b82f6',
            'description': 'Students excelling academically (GPA/Academic >= 75) but possessing low placement readiness index (< 55).',
            'criteria_summary': 'Academic Score >= 75% AND Placement Readiness < 55%',
            'recommended_focus': 'Aptitude acceleration, mock HR/technical interviews, competitive coding drills, and resume portfolio reviews.'
        },
        {
            'id': 'attendance_academic_at_risk',
            'name': 'Attendance & Academic At-Risk',
            'short_name': 'Attendance & Academic Vulnerable',
            'badge_color': '#ef4444',
            'description': 'Students facing concurrent attendance shortages (< 75%) and academic standing deficiencies (< 60%).',
            'criteria_summary': 'Attendance < 75% AND Academic Score < 60%',
            'recommended_focus': 'Immediate faculty advisory meeting, attendance condonation recovery plan, and subject remedial classes.'
        },
        {
            'id': 'all_round_placement_ready',
            'name': 'High Success & Placement Ready',
            'short_name': 'Premier Placement Ready',
            'badge_color': '#10b981',
            'description': 'Top-tier well-rounded students with high overall success scores (>= 75) and strong placement readiness (>= 70).',
            'criteria_summary': 'Success Score >= 75% AND Placement Readiness >= 70%',
            'recommended_focus': 'Tier-1 corporate recruitment referrals, hackathons, undergraduate research, and peer leadership roles.'
        },
        {
            'id': 'disengaged_high_potential',
            'name': 'Disengaged High-Potential (LMS Gap)',
            'short_name': 'High Academic / Low LMS',
            'badge_color': '#f59e0b',
            'description': 'Academically strong students (Academic >= 75) with low digital LMS and online coursework engagement (< 50).',
            'criteria_summary': 'Academic Score >= 75% AND LMS Score < 50%',
            'recommended_focus': 'Self-paced learning reminders, online quiz completion milestone incentives, and digital assignment checks.'
        },
        {
            'id': 'core_support_group',
            'name': 'Core Multi-Disciplinary Support Group',
            'short_name': 'Comprehensive Support',
            'badge_color': '#8b5cf6',
            'description': 'Students requiring comprehensive support across academic mastery (< 60), employability skills (< 50), or classified High Risk.',
            'criteria_summary': 'Academic < 60% OR Placement < 50% OR High Risk',
            'recommended_focus': 'Holistic multi-tiered mentoring, foundational skill bootcamps, and structured counselor check-ins.'
        }
    ]

    @classmethod
    def evaluate_student_segments(cls, score, student, acad_rec=None, placement_prof=None):
        """
        Determines which segments a given student belongs to and provides explanation reasons.
        """
        acad = score.academic_component or 0.0
        att = score.attendance_component or 0.0
        lms = score.lms_component or 0.0
        placement = score.placement_component or 0.0
        success = score.success_score or 0.0
        risk = score.risk_level or 'Low'

        matched_segments = []

        # 1. Academic Achievers with Placement Gap
        if acad >= 75.0 and placement < 55.0:
            matched_segments.append({
                'segment_id': 'academic_achievers_placement_gap',
                'name': 'Academic Achievers with Placement Gaps',
                'reason': f"Strong academic index ({round(acad, 1)}%) contrasted with placement readiness ({round(placement, 1)}%)."
            })

        # 2. Attendance & Academic At-Risk
        if att < 75.0 and acad < 60.0:
            matched_segments.append({
                'segment_id': 'attendance_academic_at_risk',
                'name': 'Attendance & Academic At-Risk',
                'reason': f"Attendance is {round(att, 1)}% (<75%) and academic score is {round(acad, 1)}% (<60%)."
            })

        # 3. High Success & Placement Ready
        if success >= 75.0 and placement >= 70.0:
            matched_segments.append({
                'segment_id': 'all_round_placement_ready',
                'name': 'High Success & Placement Ready',
                'reason': f"Composite success score ({round(success, 1)}) and placement readiness ({round(placement, 1)}%) both exceed target benchmarks."
            })

        # 4. Disengaged High-Potential
        if acad >= 75.0 and lms < 50.0:
            matched_segments.append({
                'segment_id': 'disengaged_high_potential',
                'name': 'Disengaged High-Potential (LMS Gap)',
                'reason': f"High academic performance ({round(acad, 1)}%) but low digital LMS course activity ({round(lms, 1)}%)."
            })

        # 5. Core Multi-Disciplinary Support Group
        if acad < 60.0 or placement < 50.0 or risk == 'High':
            matched_segments.append({
                'segment_id': 'core_support_group',
                'name': 'Core Multi-Disciplinary Support Group',
                'reason': f"Identified support triggers: Academic={round(acad, 1)}%, Placement={round(placement, 1)}%, Risk Level={risk}."
            })

        return matched_segments

    @classmethod
    def get_all_segments(cls, department=None):
        """
        Calculates all segment statistics and returns matched student rosters.
        """
        query = db.session.query(StudentScore, Student).join(Student, StudentScore.student_id == Student.student_id)
        if department:
            query = query.filter(Student.department == department)

        records = query.all()
        total_assessed = len(records)

        # Initialize segment buckets
        segment_map = {}
        for defn in cls.SEGMENT_DEFINITIONS:
            segment_map[defn['id']] = {
                'segment_id': defn['id'],
                'name': defn['name'],
                'short_name': defn['short_name'],
                'badge_color': defn['badge_color'],
                'description': defn['description'],
                'criteria_summary': defn['criteria_summary'],
                'recommended_focus': defn['recommended_focus'],
                'student_count': 0,
                'percentage': 0.0,
                'students': []
            }

        for score, student in records:
            matched = cls.evaluate_student_segments(score, student)
            for m in matched:
                seg_id = m['segment_id']
                if seg_id in segment_map:
                    segment_map[seg_id]['student_count'] += 1
                    segment_map[seg_id]['students'].append({
                        'student_id': student.student_id,
                        'student_name': student.full_name,
                        'email': student.email,
                        'department': student.department,
                        'academic_year': student.academic_year,
                        'semester': student.semester,
                        'success_score': round(score.success_score, 1),
                        'academic_score': round(score.academic_component, 1),
                        'attendance_score': round(score.attendance_component, 1),
                        'placement_score': round(score.placement_component, 1),
                        'lms_score': round(score.lms_component, 1),
                        'risk_level': score.risk_level,
                        'membership_reason': m['reason']
                    })

        segments_list = []
        for defn in cls.SEGMENT_DEFINITIONS:
            seg = segment_map[defn['id']]
            seg['percentage'] = round((seg['student_count'] / total_assessed * 100), 1) if total_assessed > 0 else 0.0
            segments_list.append(seg)

        return {
            'total_students_assessed': total_assessed,
            'segments': segments_list
        }

    @classmethod
    def get_segment_by_id(cls, segment_id, department=None):
        """
        Retrieves a single segment definition and matched student roster.
        """
        all_data = cls.get_all_segments(department=department)
        for seg in all_data['segments']:
            if seg['segment_id'] == segment_id:
                return seg
        return None
