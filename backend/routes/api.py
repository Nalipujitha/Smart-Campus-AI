from datetime import datetime, date
from flask import Blueprint, request, jsonify, session
from backend.extensions import db
from backend.models.student import Student
from backend.models.attendance import AttendanceSession, AttendanceRecord
from backend.models.intervention import Intervention
from backend.models.recommendation import Recommendation
from backend.models.learning import LearningPlan
from backend.models.placement import PlacementProfile
from backend.models.audit import StudentScore
from backend.services.institutional_analytics import InstitutionalAnalyticsService
from backend.services.attendance_service import AttendanceService
from backend.services.risk_analysis import RiskAnalysisService
from backend.services.success_score import SuccessScoreService
from backend.services.career_guidance import CareerGuidanceService
from backend.services.campus_assistant import CampusAssistantService

api_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# ----------------- DASHBOARD & ANALYTICS -----------------

@api_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    dept = request.args.get('department')
    year = request.args.get('academic_year', type=int)
    sem = request.args.get('semester', type=int)
    data = InstitutionalAnalyticsService.get_dashboard_summary(dept, year, sem)
    return jsonify(data), 200

@api_bp.route('/analytics/risk-distribution', methods=['GET'])
def get_risk_distribution():
    data = RiskAnalysisService.get_institutional_risk_summary()
    return jsonify(data), 200

@api_bp.route('/analytics/departments', methods=['GET'])
def get_department_analytics():
    summary = InstitutionalAnalyticsService.get_dashboard_summary()
    return jsonify({
        'departments': summary['department_distribution'],
        'placement_by_dept': summary['placement_by_dept'],
        'department_success_scores': summary['department_success_scores']
    }), 200

@api_bp.route('/institutional/summary', methods=['GET'])
def get_institutional_summary():
    dept = request.args.get('department')
    data = InstitutionalAnalyticsService.get_dashboard_summary(department=dept)
    return jsonify(data), 200

# ----------------- STUDENTS -----------------

@api_bp.route('/students', methods=['GET'])
def list_students():
    dept = request.args.get('department')
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = Student.query
    if dept:
        query = query.filter_by(department=dept)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (Student.student_id.ilike(f"%{search}%")) |
            (Student.first_name.ilike(f"%{search}%")) |
            (Student.last_name.ilike(f"%{search}%"))
        )

    students = query.limit(100).all()
    return jsonify([s.to_dict() for s in students]), 200

@api_bp.route('/students/<student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': 'Student not found.'}), 404
    
    score_data = SuccessScoreService.calculate_student_score(student, save_db=False)
    att_stats = AttendanceService.calculate_student_attendance(student_id)
    
    res = student.to_dict()
    res['score_details'] = score_data
    res['attendance_details'] = att_stats
    return jsonify(res), 200

@api_bp.route('/students', methods=['POST'])
def create_student():
    data = request.get_json() or {}
    sid = data.get('student_id', '').strip().upper()
    fname = data.get('first_name', '').strip()
    lname = data.get('last_name', '').strip()
    email = data.get('email', '').strip().lower()
    dept = data.get('department', 'Computer Science & Engineering')

    if not sid or not fname or not lname or not email:
        return jsonify({'error': 'Missing required student fields (student_id, first_name, last_name, email).'}), 400

    if Student.query.filter_by(student_id=sid).first():
        return jsonify({'error': f"Student ID '{sid}' already exists."}), 409

    stu = Student(
        student_id=sid,
        first_name=fname,
        last_name=lname,
        email=email,
        department=dept,
        academic_year=int(data.get('academic_year', 1)),
        semester=int(data.get('semester', 1)),
        section=data.get('section', 'A')
    )
    db.session.add(stu)
    db.session.commit()
    SuccessScoreService.calculate_student_score(stu, save_db=True)

    return jsonify(stu.to_dict()), 201

@api_bp.route('/students/<student_id>', methods=['PATCH'])
def patch_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': 'Student not found.'}), 404

    data = request.get_json() or {}
    if 'first_name' in data:
        student.first_name = data['first_name']
    if 'last_name' in data:
        student.last_name = data['last_name']
    if 'department' in data:
        student.department = data['department']
    if 'status' in data:
        student.status = data['status']

    db.session.commit()
    return jsonify(student.to_dict()), 200

@api_bp.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': 'Student not found.'}), 404

    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': f"Student {student_id} successfully deleted."}), 200

# ----------------- ATTENDANCE -----------------

@api_bp.route('/attendance/sessions', methods=['GET'])
def list_attendance_sessions():
    sessions = AttendanceSession.query.order_by(AttendanceSession.session_date.desc()).limit(50).all()
    return jsonify([s.to_dict() for s in sessions]), 200

@api_bp.route('/attendance/sessions', methods=['POST'])
def create_attendance_session():
    data = request.get_json() or {}
    dept = data.get('department')
    sem = data.get('semester')
    subject = data.get('subject')
    records = data.get('records', [])

    if not dept or not sem or not subject or not records:
        return jsonify({'error': 'Department, semester, subject, and records are mandatory.'}), 400

    session_date = data.get('session_date', date.today().isoformat())
    faculty_id = session.get('user_id')

    try:
        sess = AttendanceService.create_session_with_records(
            department=dept,
            class_code=data.get('class_code', f"{dept[:3].upper()}-SEM{sem}"),
            semester=sem,
            subject=subject,
            session_date=session_date,
            faculty_id=faculty_id,
            records_data=records,
            time_slot=data.get('time_slot')
        )
        return jsonify(sess.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/attendance/sessions/<int:session_id>', methods=['GET'])
def get_attendance_session(session_id):
    sess = AttendanceSession.query.get(session_id)
    if not sess:
        return jsonify({'error': 'Session not found.'}), 404
    
    records = AttendanceRecord.query.filter_by(session_id=session_id).all()
    res = sess.to_dict()
    res['records'] = [r.to_dict() for r in records]
    return jsonify(res), 200

@api_bp.route('/attendance/students/<student_id>', methods=['GET'])
def get_student_attendance(student_id):
    stats = AttendanceService.calculate_student_attendance(student_id)
    return jsonify(stats), 200

@api_bp.route('/attendance/reports', methods=['GET'])
def get_attendance_reports():
    summary = AttendanceService.get_attendance_summary()
    alerts = AttendanceService.get_attendance_alerts()
    return jsonify({'summary': summary, 'alerts': alerts}), 200

# ----------------- INTERVENTIONS -----------------

@api_bp.route('/interventions', methods=['GET'])
def list_interventions():
    interventions = Intervention.query.order_by(Intervention.session_date.desc()).all()
    return jsonify([i.to_dict() for i in interventions]), 200

@api_bp.route('/interventions', methods=['POST'])
def create_intervention():
    data = request.get_json() or {}
    sid = data.get('student_id')
    title = data.get('title')
    notes = data.get('notes')

    if not sid or not title or not notes:
        return jsonify({'error': 'student_id, title, and notes are required.'}), 400

    inv = Intervention(
        student_id=sid,
        faculty_id=session.get('user_id'),
        title=title,
        category=data.get('category', 'Academic'),
        priority=data.get('priority', 'Medium'),
        status='Open',
        session_date=date.today(),
        notes=notes,
        action_items=data.get('action_items')
    )
    db.session.add(inv)
    db.session.commit()
    return jsonify(inv.to_dict()), 201

@api_bp.route('/interventions/<int:intervention_id>', methods=['PATCH'])
def patch_intervention(intervention_id):
    inv = Intervention.query.get(intervention_id)
    if not inv:
        return jsonify({'error': 'Intervention not found.'}), 404

    data = request.get_json() or {}
    if 'status' in data:
        inv.status = data['status']
    if 'priority' in data:
        inv.priority = data['priority']
    if 'outcome_notes' in data:
        inv.outcome_notes = data['outcome_notes']

    inv.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(inv.to_dict()), 200

from backend.services.segmentation import StudentSegmentationService
from backend.services.recommendations import RecommendationService

@api_bp.route('/interventions/record', methods=['POST'])
def record_intervention_followup():
    data = request.get_json() or {}
    sid = data.get('student_id')
    title = data.get('title', 'Faculty Intervention / Follow-up')
    notes = data.get('notes')

    if not sid or not notes:
        return jsonify({'error': 'student_id and notes are required fields.'}), 400

    student = Student.query.filter_by(student_id=sid).first()
    if not student:
        return jsonify({'error': f"Student '{sid}' not found."}), 404

    follow_up_str = data.get('follow_up_date')
    follow_up_d = None
    if follow_up_str:
        try:
            follow_up_d = datetime.strptime(follow_up_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    inv = Intervention(
        student_id=sid,
        faculty_id=session.get('user_id'),
        title=title,
        category=data.get('category', 'Academic'),
        priority=data.get('priority', 'Medium'),
        status=data.get('status', 'Open'),
        session_date=date.today(),
        follow_up_date=follow_up_d,
        notes=notes,
        action_items=data.get('action_items', ''),
        outcome_notes=data.get('outcome_notes', '')
    )
    db.session.add(inv)
    db.session.commit()
    return jsonify({'message': 'Intervention record logged successfully.', 'intervention': inv.to_dict()}), 201

# ----------------- AT-RISK STUDENTS & SEGMENTATION -----------------

@api_bp.route('/analytics/at-risk-students', methods=['GET'])
def get_at_risk_students():
    dept = request.args.get('department')
    level = request.args.get('risk_level')
    search = request.args.get('search')
    immediate_only = request.args.get('immediate_only', 'false').lower() in ['true', '1', 'yes']
    limit = request.args.get('limit', 200, type=int)

    students = RiskAnalysisService.get_at_risk_students(
        department=dept,
        risk_level=level,
        search=search,
        immediate_only=immediate_only,
        limit=limit
    )
    return jsonify({
        'count': len(students),
        'filters': {
            'department': dept,
            'risk_level': level,
            'search': search,
            'immediate_only': immediate_only
        },
        'students': students
    }), 200

@api_bp.route('/analytics/segments', methods=['GET'])
def get_student_segments():
    dept = request.args.get('department')
    data = StudentSegmentationService.get_all_segments(department=dept)
    return jsonify(data), 200

@api_bp.route('/analytics/segments/<segment_id>', methods=['GET'])
def get_segment_details(segment_id):
    dept = request.args.get('department')
    seg = StudentSegmentationService.get_segment_by_id(segment_id, department=dept)
    if not seg:
        return jsonify({'error': f"Segment '{segment_id}' not found."}), 404
    return jsonify(seg), 200

@api_bp.route('/students/<student_id>/score-breakdown', methods=['GET'])
def get_student_score_breakdown(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': f"Student '{student_id}' not found."}), 404

    score_data = SuccessScoreService.calculate_student_score(student, save_db=False)
    segments = StudentSegmentationService.evaluate_student_segments(
        StudentScore.query.filter_by(student_id=student_id).first() or type('obj', (), score_data),
        student
    )
    score_data['matched_segments'] = segments
    return jsonify(score_data), 200

# ----------------- RECOMMENDATIONS & FOLLOW-UP -----------------

@api_bp.route('/recommendations/<int:rec_id>/status', methods=['POST', 'PATCH'])
def update_recommendation_status_api(rec_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'status field is required.'}), 400

    try:
        updated = RecommendationService.update_recommendation_status(rec_id, new_status)
        if not updated:
            return jsonify({'error': 'Recommendation not found.'}), 404
        return jsonify({'message': 'Status updated successfully.', 'recommendation': updated.to_dict()}), 200
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400

# ----------------- ADDITIONAL MODULES -----------------

@api_bp.route('/students/<student_id>/recommendations', methods=['GET'])
def get_student_recommendations(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({'error': 'Student not found.'}), 404
    recs = Recommendation.query.filter_by(student_id=student_id).order_by(Recommendation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in recs]), 200

@api_bp.route('/career/recommendations', methods=['GET'])
def get_career_recommendations():
    skills = request.args.get('skills', 'Python, SQL, Git')
    role = request.args.get('role', 'Software Developer')
    analysis = CareerGuidanceService.analyze_career_path(skills, role)
    return jsonify(analysis), 200

@api_bp.route('/learning/plans', methods=['GET'])
def get_learning_plans():
    sid = request.args.get('student_id')
    query = LearningPlan.query
    if sid:
        query = query.filter_by(student_id=sid)
    plans = query.all()
    return jsonify([p.to_dict() for p in plans]), 200

@api_bp.route('/placement/readiness', methods=['GET'])
def get_placement_readiness():
    sid = request.args.get('student_id')
    if sid:
        prof = PlacementProfile.query.filter_by(student_id=sid).first()
        return jsonify(prof.to_dict() if prof else {}), 200
    
    profiles = PlacementProfile.query.all()
    return jsonify([p.to_dict() for p in profiles]), 200

@api_bp.route('/campus/ask', methods=['POST'])
def campus_ask():
    data = request.get_json() or {}
    q = data.get('question', '')
    res = CampusAssistantService.query(q)
    return jsonify(res), 200

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat_v1():
    from backend.routes.ai_chat import chat
    return chat()


