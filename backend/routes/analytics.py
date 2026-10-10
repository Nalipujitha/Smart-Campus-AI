from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.services.risk_analysis import RiskAnalysisService
from backend.services.institutional_analytics import InstitutionalAnalyticsService
from backend.services.success_score import SuccessScoreService
from backend.services.segmentation import StudentSegmentationService
from backend.models.student import Student
from backend.models.audit import StudentScore

analytics_bp = Blueprint('analytics', __name__)

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Electronics & Communication',
    'Information Technology',
    'Artificial Intelligence & Data Science',
    'Mechanical Engineering'
]

@analytics_bp.route('/risk')
@login_required
def risk_analysis():
    user = get_current_user()
    dept = request.args.get('department')
    level = request.args.get('risk_level')
    search = request.args.get('search')
    immediate_only = request.args.get('immediate_only', 'false').lower() in ['true', '1', 'yes']

    at_risk_students = RiskAnalysisService.get_at_risk_students(
        department=dept,
        risk_level=level,
        search=search,
        immediate_only=immediate_only
    )
    risk_summary = RiskAnalysisService.get_institutional_risk_summary()

    return render_template(
        'risk_analysis.html',
        user=user,
        at_risk_students=at_risk_students,
        risk_summary=risk_summary,
        departments=DEPARTMENTS,
        selected_dept=dept,
        selected_level=level,
        search_query=search,
        immediate_only=immediate_only
    )

@analytics_bp.route('/segmentation')
@login_required
def segmentation_view():
    user = get_current_user()
    dept = request.args.get('department')
    selected_segment_id = request.args.get('segment_id')

    segments_data = StudentSegmentationService.get_all_segments(department=dept)

    return render_template(
        'segmentation.html',
        user=user,
        segments=segments_data['segments'],
        total_assessed=segments_data['total_students_assessed'],
        departments=DEPARTMENTS,
        selected_dept=dept,
        selected_segment_id=selected_segment_id
    )

@analytics_bp.route('/institutional')
@login_required
@roles_required('Admin', 'Faculty', 'Placement_Officer')
def institutional_insights():
    user = get_current_user()
    dept = request.args.get('department')
    year = request.args.get('academic_year', type=int)
    sem = request.args.get('semester', type=int)

    summary = InstitutionalAnalyticsService.get_dashboard_summary(
        department=dept,
        academic_year=year,
        semester=sem
    )

    return render_template(
        'institutional_insights.html',
        user=user,
        summary=summary,
        departments=DEPARTMENTS,
        selected_dept=dept,
        selected_year=year,
        selected_sem=sem
    )

@analytics_bp.route('/recalculate-scores', methods=['POST'])
@login_required
@roles_required('Admin')
def recalculate_scores():
    SuccessScoreService.recalculate_all_scores()
    flash("Institutional student success scores recalculated across all dimensions.", "success")
    return redirect(request.referrer or url_for('analytics.risk_analysis'))
