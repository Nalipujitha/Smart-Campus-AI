import io
import csv
import sys
import time
import subprocess
import tempfile
import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.user import User
from backend.models.student import Student
from backend.models.academic import AcademicRecord
from backend.models.attendance import AttendanceRecord
from backend.models.placement import (
    PlacementProfile, PracticeQuestion, PracticeAttempt,
    Company, JobOpportunity, JobApplication, PlacementOffer
)
from backend.models.audit import AuditEvent
from backend.services.placement_service import PlacementService
from backend.services.attendance_service import AttendanceService
from backend.extensions import db

placement_bp = Blueprint('placement', __name__)

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Electronics & Communication',
    'Information Technology',
    'Artificial Intelligence & Data Science',
    'Mechanical Engineering'
]

STANDARD_CODING_PROBLEMS = [
    {
        'id': 'two_sum',
        'title': 'Two Sum Problem',
        'difficulty': 'Easy',
        'description': 'Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.',
        'template': """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []

# Test execution:
nums = [2, 7, 11, 15]
target = 9
print(two_sum(nums, target))
""",
        'expected_output': '[0, 1]'
    },
    {
        'id': 'binary_search',
        'title': 'Binary Search Algorithm',
        'difficulty': 'Medium',
        'description': 'Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return -1.',
        'template': """def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Test execution:
arr = [1, 3, 5, 7, 9, 11, 13]
print(binary_search(arr, 7))
""",
        'expected_output': '3'
    },
    {
        'id': 'valid_parentheses',
        'title': 'Valid Parentheses',
        'difficulty': 'Easy',
        'description': 'Given a string `s` containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine if the input string is valid.',
        'template': """def is_valid_parentheses(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack

# Test execution:
print(is_valid_parentheses("({[]})"))
""",
        'expected_output': 'True'
    },
    {
        'id': 'reverse_string',
        'title': 'Reverse String in Place',
        'difficulty': 'Easy',
        'description': 'Write a function that reverses a string or array in place with O(1) extra memory.',
        'template': """def reverse_words(s):
    return " ".join(s.split()[::-1])

# Test execution:
print(reverse_words("Smart Campus Analytics Platform"))
""",
        'expected_output': 'Platform Analytics Campus Smart'
    }
]

# =====================================================================
# 1. PLACEMENT DASHBOARD
# =====================================================================
@placement_bp.route('/dashboard')
@login_required
@roles_required('Placement_Officer')
def dashboard():
    user = get_current_user()
    
    profiles = PlacementProfile.query.all()
    total_students = len(profiles)
    
    # Placement eligible count (Readiness >= 60%)
    eligible_students_count = len([p for p in profiles if p.readiness_percentage >= 60.0])
    registered_students_count = JobApplication.query.with_entities(JobApplication.student_id).distinct().count()
    
    companies_count = Company.query.count()
    active_drives_count = JobOpportunity.query.filter_by(status='Active').count()
    applications_in_progress = JobApplication.query.filter(JobApplication.stage.in_(['Applied', 'Shortlisted', 'Interview'])).count()
    total_offers = PlacementOffer.query.count()
    needs_prep_count = len([p for p in profiles if p.readiness_percentage < 60.0])

    avg_readiness = round(sum(p.readiness_percentage for p in profiles) / total_students, 1) if total_students > 0 else 0.0
    placed_students = len([p for p in profiles if p.placement_status == 'Placed'])
    placement_rate = round((placed_students / total_students * 100), 1) if total_students > 0 else 0.0

    # Applications pipeline breakdown
    pipeline = {
        'Applied': JobApplication.query.filter_by(stage='Applied').count(),
        'Shortlisted': JobApplication.query.filter_by(stage='Shortlisted').count(),
        'Interview': JobApplication.query.filter_by(stage='Interview').count(),
        'Selected': JobApplication.query.filter_by(stage='Selected').count(),
        'Offer Accepted': JobApplication.query.filter_by(stage='Offer Accepted').count()
    }

    # Recent opportunities
    recent_jobs = JobOpportunity.query.order_by(JobOpportunity.created_at.desc()).limit(5).all()
    recent_offers = PlacementOffer.query.order_by(PlacementOffer.offer_date.desc()).limit(5).all()

    return render_template(
        'placement/dashboard.html',
        user=user,
        total_students=total_students,
        eligible_students_count=eligible_students_count,
        registered_students_count=registered_students_count,
        companies_count=companies_count,
        active_drives_count=active_drives_count,
        applications_in_progress=applications_in_progress,
        total_offers=total_offers,
        needs_prep_count=needs_prep_count,
        avg_readiness=avg_readiness,
        placement_rate=placement_rate,
        pipeline=pipeline,
        recent_jobs=recent_jobs,
        recent_offers=recent_offers,
        last_refresh=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

# =====================================================================
# 2. STUDENT PLACEMENT DIRECTORY
# =====================================================================
@placement_bp.route('/students')
@login_required
@roles_required('Placement_Officer')
def students():
    user = get_current_user()
    dept = request.args.get('department')
    role_filter = request.args.get('target_role')
    status_filter = request.args.get('status')
    page = request.args.get('page', 1, type=int)

    query = PlacementProfile.query.join(Student)
    if dept:
        query = query.filter(Student.department == dept)
    if role_filter:
        query = query.filter(PlacementProfile.target_role.ilike(f"%{role_filter}%"))
    if status_filter:
        query = query.filter(PlacementProfile.placement_status == status_filter)

    profiles_paginated = query.order_by(PlacementProfile.readiness_percentage.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'placement/students.html',
        user=user,
        profiles=profiles_paginated.items,
        pagination=profiles_paginated,
        departments=DEPARTMENTS,
        selected_dept=dept,
        selected_status=status_filter
    )

# =====================================================================
# 3. PLACEMENT ELIGIBILITY CRITERIA ENGINE
# =====================================================================
@placement_bp.route('/eligibility')
@login_required
@roles_required('Placement_Officer')
def eligibility():
    user = get_current_user()
    min_cgpa = float(request.args.get('min_cgpa', 6.5))
    min_readiness = float(request.args.get('min_readiness', 60.0))
    min_attendance = float(request.args.get('min_attendance', 75.0))
    dept = request.args.get('department')

    all_students = Student.query.all()
    if dept:
        all_students = [s for s in all_students if s.department == dept]

    evaluated_candidates = []
    eligible_count = 0

    for s in all_students:
        prof = PlacementProfile.query.filter_by(student_id=s.student_id).first()
        readiness = prof.readiness_percentage if prof else 0.0
        
        # Latest CGPA
        acad = AcademicRecord.query.filter_by(student_id=s.student_id).order_by(AcademicRecord.semester.desc()).first()
        cgpa = acad.cgpa if acad and acad.cgpa else (acad.gpa if acad else 7.0)
        backlogs = acad.backlogs_count if acad else 0
        
        # Attendance
        att = AttendanceService.calculate_student_attendance(s.student_id)
        att_pct = att['percentage']

        # Determine reasons
        reasons = []
        is_eligible = True

        if cgpa < min_cgpa:
            is_eligible = False
            reasons.append(f"CGPA ({cgpa}) below cutoff {min_cgpa}")
        if readiness < min_readiness:
            is_eligible = False
            reasons.append(f"Readiness ({readiness}%) below cutoff {min_readiness}%")
        if att_pct < min_attendance:
            is_eligible = False
            reasons.append(f"Attendance ({att_pct}%) below cutoff {min_attendance}%")
        if backlogs > 0:
            is_eligible = False
            reasons.append(f"{backlogs} active backlogs")

        if is_eligible:
            eligible_count += 1

        evaluated_candidates.append({
            'student': s,
            'profile': prof,
            'cgpa': cgpa,
            'readiness': readiness,
            'attendance': att_pct,
            'backlogs': backlogs,
            'is_eligible': is_eligible,
            'reasons': reasons
        })

    return render_template(
        'placement/eligibility.html',
        user=user,
        evaluated_candidates=evaluated_candidates,
        eligible_count=eligible_count,
        total_count=len(all_students),
        min_cgpa=min_cgpa,
        min_readiness=min_readiness,
        min_attendance=min_attendance,
        departments=DEPARTMENTS,
        selected_dept=dept
    )

# =====================================================================
# 4. COMPANY MANAGEMENT
# =====================================================================
@placement_bp.route('/companies', methods=['GET', 'POST'])
@login_required
@roles_required('Placement_Officer')
def companies():
    user = get_current_user()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        industry = request.form.get('industry', 'Information Technology').strip()
        website = request.form.get('website', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        min_cgpa = float(request.form.get('min_cgpa', 6.0))
        eligible_depts = request.form.get('eligible_departments', 'Computer Science & Engineering')
        required_skills = request.form.get('required_skills', '')

        if not name:
            flash("Company name is required.", "danger")
            return redirect(url_for('placement.companies'))

        if Company.query.filter_by(name=name).first():
            flash(f"Company '{name}' already exists in registry.", "danger")
            return redirect(url_for('placement.companies'))

        new_comp = Company(
            name=name,
            industry=industry,
            website=website,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone,
            min_cgpa=min_cgpa,
            eligible_departments=eligible_depts,
            required_skills=required_skills,
            status='Active'
        )
        db.session.add(new_comp)

        db.session.add(AuditEvent(
            user_id=user.id,
            action="ADD_COMPANY",
            module="Placement Companies",
            details=f"Placement Officer registered company partner '{name}'.",
            ip_address=request.remote_addr
        ))
        db.session.commit()
        flash(f"Recruitment partner '{name}' added successfully.", "success")
        return redirect(url_for('placement.companies'))

    companies_list = Company.query.order_by(Company.created_at.desc()).all()
    return render_template(
        'placement/companies.html',
        user=user,
        companies=companies_list,
        departments=DEPARTMENTS
    )

# =====================================================================
# 5. JOBS & RECRUITMENT DRIVES
# =====================================================================
@placement_bp.route('/jobs', methods=['GET', 'POST'])
@login_required
@roles_required('Placement_Officer')
def jobs():
    user = get_current_user()

    if request.method == 'POST':
        company_id = int(request.form.get('company_id'))
        title = request.form.get('title', '').strip()
        role_type = request.form.get('role_type', 'Full-time')
        location = request.form.get('location', 'Bengaluru / Hybrid')
        ctc = request.form.get('ctc_package', '8.0 LPA')
        min_cgpa = float(request.form.get('min_cgpa', 6.5))
        min_readiness = float(request.form.get('min_readiness', 60.0))
        depts = request.form.get('eligible_departments', 'Computer Science & Engineering')
        skills = request.form.get('required_skills', 'Python, SQL')
        deadline_str = request.form.get('application_deadline')
        drive_str = request.form.get('drive_date')

        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
        except Exception:
            deadline = None

        try:
            drive_date = datetime.strptime(drive_str, '%Y-%m-%d').date() if drive_str else None
        except Exception:
            drive_date = None

        job = JobOpportunity(
            company_id=company_id,
            title=title,
            role_type=role_type,
            location=location,
            ctc_package=ctc,
            min_cgpa=min_cgpa,
            min_readiness=min_readiness,
            eligible_departments=depts,
            required_skills=skills,
            application_deadline=deadline,
            drive_date=drive_date,
            status='Active'
        )
        db.session.add(job)
        db.session.commit()
        flash(f"Job opportunity '{title}' posted successfully.", "success")
        return redirect(url_for('placement.jobs'))

    jobs_list = JobOpportunity.query.order_by(JobOpportunity.created_at.desc()).all()
    companies_list = Company.query.filter_by(status='Active').all()

    return render_template(
        'placement/jobs.html',
        user=user,
        jobs=jobs_list,
        companies=companies_list,
        departments=DEPARTMENTS
    )

@placement_bp.route('/drives')
@login_required
@roles_required('Placement_Officer')
def drives():
    user = get_current_user()
    active_drives = JobOpportunity.query.filter(JobOpportunity.drive_date != None).order_by(JobOpportunity.drive_date.asc()).all()
    return render_template(
        'placement/drives.html',
        user=user,
        drives=active_drives
    )

# =====================================================================
# 6. CANDIDATES & APPLICATION PIPELINE
# =====================================================================
@placement_bp.route('/candidates')
@login_required
@roles_required('Placement_Officer')
def candidates():
    user = get_current_user()
    job_id = request.args.get('job_id', type=int)
    
    jobs = JobOpportunity.query.filter_by(status='Active').all()
    selected_job = JobOpportunity.query.get(job_id) if job_id else (jobs[0] if jobs else None)

    candidates_list = []
    if selected_job:
        # Match students who meet criteria
        students = Student.query.filter(Student.semester >= 5).all()
        for s in students:
            prof = PlacementProfile.query.filter_by(student_id=s.student_id).first()
            readiness = prof.readiness_percentage if prof else 0.0
            
            # Check if already applied
            app = JobApplication.query.filter_by(student_id=s.student_id, job_id=selected_job.id).first()

            candidates_list.append({
                'student': s,
                'profile': prof,
                'readiness': readiness,
                'application': app
            })

    return render_template(
        'placement/candidates.html',
        user=user,
        jobs=jobs,
        selected_job=selected_job,
        candidates=candidates_list
    )

@placement_bp.route('/applications')
@login_required
@roles_required('Placement_Officer')
def applications():
    user = get_current_user()
    stage_filter = request.args.get('stage')
    
    query = JobApplication.query
    if stage_filter:
        query = query.filter_by(stage=stage_filter)
        
    apps = query.order_by(JobApplication.updated_at.desc()).all()

    return render_template(
        'placement/applications.html',
        user=user,
        applications=apps,
        selected_stage=stage_filter
    )

@placement_bp.route('/applications/<int:app_id>/update-stage', methods=['POST'])
@login_required
@roles_required('Placement_Officer')
def update_application_stage(app_id):
    user = get_current_user()
    app = JobApplication.query.get_or_404(app_id)
    new_stage = request.form.get('stage')
    feedback = request.form.get('feedback', '')

    if new_stage in ['Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected', 'Offer Accepted']:
        app.stage = new_stage
        if feedback:
            app.feedback = feedback
        
        # If Selected or Offer Accepted, create Placement Offer
        if new_stage in ['Selected', 'Offer Accepted']:
            if not PlacementOffer.query.filter_by(student_id=app.student_id, job_title=app.job.title).first():
                db.session.add(PlacementOffer(
                    student_id=app.student_id,
                    company_id=app.job.company_id,
                    company_name=app.job.company.name if app.job.company else 'Recruiter',
                    job_title=app.job.title,
                    ctc_package=app.job.ctc_package,
                    ctc_numeric=float(app.job.ctc_package.replace(' LPA', '').strip()) if 'LPA' in app.job.ctc_package else 8.0,
                    offer_date=date.today(),
                    status='Accepted' if new_stage == 'Offer Accepted' else 'Offered'
                ))
                prof = PlacementProfile.query.filter_by(student_id=app.student_id).first()
                if prof:
                    prof.placement_status = 'Placed'

        db.session.commit()
        flash(f"Application stage for {app.student_id} updated to {new_stage}.", "success")

    return redirect(url_for('placement.applications'))

# =====================================================================
# 7. OFFERS & OUTCOMES
# =====================================================================
@placement_bp.route('/offers', methods=['GET', 'POST'])
@login_required
@roles_required('Placement_Officer')
def offers():
    user = get_current_user()

    if request.method == 'POST':
        stu_id = request.form.get('student_id', '').strip().upper()
        comp_name = request.form.get('company_name', '').strip()
        job_title = request.form.get('job_title', '').strip()
        ctc_pkg = request.form.get('ctc_package', '10.0 LPA').strip()
        status_val = request.form.get('status', 'Offered')

        if not stu_id or not comp_name or not job_title:
            flash("Student ID, Company Name, and Job Title are required.", "danger")
            return redirect(url_for('placement.offers'))

        ctc_num = float(ctc_pkg.replace(' LPA', '').strip()) if 'LPA' in ctc_pkg else 8.0

        offer = PlacementOffer(
            student_id=stu_id,
            company_name=comp_name,
            job_title=job_title,
            ctc_package=ctc_pkg,
            ctc_numeric=ctc_num,
            offer_date=date.today(),
            status=status_val
        )
        db.session.add(offer)

        prof = PlacementProfile.query.filter_by(student_id=stu_id).first()
        if prof:
            prof.placement_status = 'Placed'

        db.session.commit()
        flash(f"Placement offer from {comp_name} ({ctc_pkg}) logged for student {stu_id}.", "success")
        return redirect(url_for('placement.offers'))

    offers_list = PlacementOffer.query.order_by(PlacementOffer.offer_date.desc()).all()
    companies_list = Company.query.all()

    return render_template(
        'placement/offers.html',
        user=user,
        offers=offers_list,
        companies=companies_list
    )

# =====================================================================
# 8. PLACEMENT PREPARATION (APTITUDE, INTERVIEW, READINESS, EDITOR)
# =====================================================================
@placement_bp.route('/')
@login_required
def index():
    user = get_current_user()
    if user.role == 'Placement_Officer':
        return redirect(url_for('placement.dashboard'))

    target_student_id = user.student_id if user.role == 'Student' else request.args.get('student_id', 'STU2024001')
    student = Student.query.filter_by(student_id=target_student_id).first()
    summary = PlacementService.get_student_placement_summary(target_student_id)
    
    category = request.args.get('category', 'Aptitude')
    difficulty = request.args.get('difficulty')
    questions = PlacementService.get_questions(category=category, difficulty=difficulty)
    all_students = Student.query.filter_by(status='Active').order_by(Student.student_id.asc()).limit(50).all()

    return render_template(
        'placement.html',
        user=user,
        student=student,
        summary=summary,
        questions=questions,
        selected_category=category,
        selected_difficulty=difficulty,
        all_students=all_students,
        selected_student_id=target_student_id,
        coding_problems=STANDARD_CODING_PROBLEMS
    )

@placement_bp.route('/aptitude')
@login_required
def aptitude():
    user = get_current_user()
    category = 'Aptitude'
    difficulty = request.args.get('difficulty')
    questions = PlacementService.get_questions(category=category, difficulty=difficulty)

    return render_template(
        'placement/aptitude.html',
        user=user,
        questions=questions,
        selected_difficulty=difficulty
    )

@placement_bp.route('/interviews')
@login_required
def interviews():
    user = get_current_user()
    questions = PlacementService.get_questions(category='Interview')
    return render_template('placement/interviews.html', user=user, questions=questions)

@placement_bp.route('/readiness')
@login_required
def readiness():
    user = get_current_user()
    profiles = PlacementProfile.query.order_by(PlacementProfile.readiness_percentage.desc()).limit(50).all()
    return render_template('placement/readiness.html', user=user, profiles=profiles)

@placement_bp.route('/editor')
@login_required
def editor():
    user = get_current_user()
    target_student_id = user.student_id if user.role == 'Student' else request.args.get('student_id', 'STU2024001')
    student = Student.query.filter_by(student_id=target_student_id).first()
    problem_id = request.args.get('problem', 'two_sum')
    selected_prob = next((p for p in STANDARD_CODING_PROBLEMS if p['id'] == problem_id), STANDARD_CODING_PROBLEMS[0])

    return render_template(
        'code_editor.html',
        user=user,
        student=student,
        problems=STANDARD_CODING_PROBLEMS,
        selected_problem=selected_prob
    )

@placement_bp.route('/execute-code', methods=['POST'])
@login_required
def execute_code():
    data = request.get_json() if request.is_json else request.form
    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    input_text = data.get('input', '')
    student_id = data.get('student_id')
    user = get_current_user()

    if user.role == 'Student':
        student_id = user.student_id

    if not code.strip():
        return jsonify({'error': 'No code provided for execution.'}), 400

    start_time = time.time()
    stdout = ""
    stderr = ""
    status = "success"

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_filename = f.name

        proc = subprocess.run(
            [sys.executable, temp_filename],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=5
        )
        stdout = proc.stdout
        stderr = proc.stderr
        if proc.returncode != 0:
            status = "error"

        try:
            os.remove(temp_filename)
        except Exception:
            pass

    except subprocess.TimeoutExpired:
        status = "timeout"
        stderr = "Execution timed out (5s limit exceeded)."
    except Exception as e:
        status = "error"
        stderr = str(e)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    if status == "success" and student_id:
        profile = PlacementProfile.query.filter_by(student_id=student_id).first()
        if profile:
            profile.coding_score = min(100.0, profile.coding_score + 2.5)
            profile.calculate_readiness()
            db.session.commit()
            from backend.services.success_score import SuccessScoreService
            stu = Student.query.filter_by(student_id=student_id).first()
            if stu:
                SuccessScoreService.calculate_student_score(stu, save_db=True)

    return jsonify({
        'status': status,
        'stdout': stdout,
        'stderr': stderr,
        'execution_time_ms': duration_ms,
        'language': language
    })

@placement_bp.route('/submit', methods=['POST'])
@login_required
def submit_answer():
    user = get_current_user()
    student_id = request.form.get('student_id')
    if user.role == 'Student':
        student_id = user.student_id

    question_id = request.form.get('question_id', type=int)
    user_answer = request.form.get('user_answer', '').strip()

    if not question_id or not user_answer:
        flash("Please select or enter an answer before submitting.", "warning")
        return redirect(url_for('placement.index', student_id=student_id))

    attempt, err = PlacementService.submit_practice_answer(
        student_id=student_id,
        question_id=question_id,
        user_answer=user_answer
    )

    if err:
        flash(err, "danger")
    else:
        if attempt.is_correct:
            flash(f"✅ Correct! {attempt.feedback}", "success")
        else:
            flash(f"❌ {attempt.feedback}", "danger")

    return redirect(url_for('placement.index', student_id=student_id))

# =====================================================================
# 9. PLACEMENT ANALYTICS & REPORTS
# =====================================================================
@placement_bp.route('/analytics')
@login_required
@roles_required('Placement_Officer')
def analytics():
    user = get_current_user()
    offers = PlacementOffer.query.all()
    companies = Company.query.all()
    profiles = PlacementProfile.query.all()

    avg_pkg = round(sum(o.ctc_numeric for o in offers) / len(offers), 2) if offers else 0.0
    highest_pkg = max((o.ctc_numeric for o in offers), default=0.0)
    total_placed = len([p for p in profiles if p.placement_status == 'Placed'])

    return render_template(
        'placement/analytics.html',
        user=user,
        offers=offers,
        companies=companies,
        avg_pkg=avg_pkg,
        highest_pkg=highest_pkg,
        total_placed=total_placed,
        total_students=len(profiles)
    )

@placement_bp.route('/reports')
@login_required
@roles_required('Placement_Officer')
def reports():
    user = get_current_user()
    return render_template('placement/reports.html', user=user)

@placement_bp.route('/reports/export/<report_type>')
@login_required
@roles_required('Placement_Officer')
def export_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'directory':
        writer.writerow(['Student ID', 'Full Name', 'Department', 'Target Role', 'Readiness %', 'Coding', 'Aptitude', 'Status'])
        for p in PlacementProfile.query.all():
            writer.writerow([p.student_id, p.student.full_name if p.student else '', p.student.department if p.student else '', p.target_role, p.readiness_percentage, p.coding_score, p.aptitude_score, p.placement_status])
        filename = f"placement_directory_{date.today()}.csv"

    elif report_type == 'applications':
        writer.writerow(['Student ID', 'Student Name', 'Job Title', 'Company', 'Stage', 'Applied Date'])
        for a in JobApplication.query.all():
            writer.writerow([a.student_id, a.student.full_name if a.student else '', a.job.title if a.job else '', a.job.company.name if (a.job and a.job.company) else '', a.stage, a.applied_at])
        filename = f"job_applications_{date.today()}.csv"

    elif report_type == 'offers':
        writer.writerow(['Student ID', 'Student Name', 'Company Name', 'Job Title', 'CTC Package', 'Offer Date', 'Status'])
        for o in PlacementOffer.query.all():
            writer.writerow([o.student_id, o.student.full_name if o.student else '', o.company_name, o.job_title, o.ctc_package, o.offer_date, o.status])
        filename = f"placement_offers_{date.today()}.csv"

    else:
        flash("Invalid report type.", "danger")
        return redirect(url_for('placement.reports'))

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@placement_bp.route('/profile')
@login_required
@roles_required('Placement_Officer')
def profile():
    user = get_current_user()
    return render_template('placement/profile.html', user=user)
