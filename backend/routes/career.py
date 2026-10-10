from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from backend.routes.auth import login_required, get_current_user
from backend.services.career_guidance import CareerGuidanceService
from backend.models.placement import PlacementProfile
from backend.models.student import Student
from backend.extensions import db

career_bp = Blueprint('career', __name__)

@career_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user = get_current_user()
    role_list = CareerGuidanceService.get_role_list()

    # Preload student's current skills & target role if student
    default_skills = "Python, SQL, Data Structures, Git"
    default_role = "Software Developer"

    if user.role == 'Student' and user.student_id:
        placement = PlacementProfile.query.filter_by(student_id=user.student_id).first()
        if placement:
            default_role = placement.target_role or default_role
            default_skills = placement.skills_json or default_skills

    selected_role = default_role
    selected_skills = default_skills
    proficiency = "Intermediate"
    analysis = None

    if request.method == 'POST':
        selected_role = request.form.get('target_role', default_role)
        selected_skills = request.form.get('skills', default_skills)
        proficiency = request.form.get('proficiency', 'Intermediate')

        # Save to student placement profile if logged in student
        if user.role == 'Student' and user.student_id:
            placement = PlacementProfile.query.filter_by(student_id=user.student_id).first()
            if placement:
                placement.target_role = selected_role
                placement.skills_json = selected_skills
                db.session.commit()

    analysis = CareerGuidanceService.analyze_career_path(
        user_skills=selected_skills,
        target_role=selected_role,
        proficiency=proficiency
    )

    return render_template(
        'career_guidance.html',
        user=user,
        role_list=role_list,
        selected_role=selected_role,
        selected_skills=selected_skills,
        proficiency=proficiency,
        analysis=analysis
    )
