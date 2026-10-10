"""
Coding Lab & Online Code Editor Blueprint for the Student Portal.
Provides ByteXL-inspired coding IDE, practice catalog, sandboxed runner, test evaluation,
submission history, topic mastery tracking, and placement readiness integration.
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.coding import CodingProblem, StudentCodeDraft, CodingSubmission
from backend.models.placement import PlacementProfile
from backend.services.code_executor import (
    run_custom_code,
    evaluate_submission,
    get_available_languages,
    SUPPORTED_LANGUAGES
)
from backend.routes.auth import login_required, get_current_user

coding_lab_bp = Blueprint('coding_lab', __name__)


def _get_student_context():
    """Helper to verify current user is a valid authenticated student."""
    user = get_current_user()
    if not user:
        return None, None
    student_id = session.get('student_id') or user.student_id
    if not student_id and user.role == 'Student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            student_id = student.student_id
        else:
            student_id = f"STU_{user.username}"
    elif not student_id:
        student_id = f"USER_{user.id}"
    
    student = Student.query.filter_by(student_id=student_id).first()
    return user, student



def _calculate_streak(submissions):
    """Calculates consecutive active practice days from submission timestamps."""
    if not submissions:
        return 0
    
    # Extract unique dates in descending order
    submission_dates = sorted(list(set(
        s.submitted_at.date() for s in submissions if s.submitted_at
    )), reverse=True)

    if not submission_dates:
        return 0

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Streak is active only if student practiced today or yesterday
    if submission_dates[0] != today and submission_dates[0] != yesterday:
        return 0

    streak = 0
    current_check = submission_dates[0]

    for d in submission_dates:
        if d == current_check:
            streak += 1
            current_check = current_check - timedelta(days=1)
        else:
            break
            
    return streak


def _sync_placement_coding_score(student_id):
    """
    Syncs the student's PlacementProfile coding score and readiness based on
    Coding Lab solved problems and submission success.
    """
    try:
        profile = PlacementProfile.query.filter_by(student_id=student_id).first()
        if not profile:
            profile = PlacementProfile(student_id=student_id)
            db.session.add(profile)

        # Get all distinct problems solved by student
        solved_submissions = CodingSubmission.query.filter_by(
            student_id=student_id,
            status='Accepted'
        ).all()
        solved_problem_ids = set(s.problem_id for s in solved_submissions)
        total_problems = CodingProblem.query.count() or 1

        # Calculate coding mastery score: 50% based on problems solved ratio + 50% based on average submission score
        solved_ratio = min(1.0, len(solved_problem_ids) / max(1, min(total_problems, 20)))
        
        all_subs = CodingSubmission.query.filter_by(student_id=student_id).all()
        if all_subs:
            avg_sub_score = sum(s.score for s in all_subs) / len(all_subs)
            # Normalize to 100 scale (each problem max score is 10-25)
            normalized_avg = min(100.0, avg_sub_score * 5.0)
        else:
            normalized_avg = 0.0

        coding_score = round((solved_ratio * 60.0) + (normalized_avg * 0.4), 1)
        profile.coding_score = min(100.0, max(profile.coding_score or 0.0, coding_score))
        profile.calculate_readiness()
        db.session.commit()
    except Exception as e:
        db.session.rollback()


# ============================================================================
# 1. CODING LAB DASHBOARD (/student/coding-lab)
# ============================================================================
@coding_lab_bp.route('/student/coding-lab')
@login_required
def dashboard():
    """Main Coding Lab dashboard showing stats, streak, topic mastery, and recommendations."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    # Fetch submissions
    submissions = CodingSubmission.query.filter_by(student_id=student_id).order_by(CodingSubmission.submitted_at.desc()).all()
    
    total_submissions = len(submissions)
    accepted_submissions = [s for s in submissions if s.status == 'Accepted']
    
    # Distinct problems attempted and solved
    attempted_problem_ids = set(s.problem_id for s in submissions)
    solved_problem_ids = set(s.problem_id for s in accepted_submissions)
    
    problems_attempted_count = len(attempted_problem_ids)
    problems_solved_count = len(solved_problem_ids)
    
    success_rate = round((len(accepted_submissions) / total_submissions * 100), 1) if total_submissions > 0 else 0.0
    current_streak = _calculate_streak(submissions)

    # All problems in library
    all_problems = CodingProblem.query.order_by(CodingProblem.id.asc()).all()
    total_problems_count = len(all_problems)

    # Difficulty stats
    difficulty_stats = {
        'Easy': {'total': 0, 'solved': 0},
        'Medium': {'total': 0, 'solved': 0},
        'Hard': {'total': 0, 'solved': 0}
    }
    
    # Topic progress stats
    topic_map = {}
    for p in all_problems:
        diff = p.difficulty if p.difficulty in difficulty_stats else 'Easy'
        difficulty_stats[diff]['total'] += 1
        if p.id in solved_problem_ids:
            difficulty_stats[diff]['solved'] += 1

        top = p.topic or 'General'
        if top not in topic_map:
            topic_map[top] = {'total': 0, 'solved': 0, 'attempted': 0}
        topic_map[top]['total'] += 1
        if p.id in solved_problem_ids:
            topic_map[top]['solved'] += 1
        elif p.id in attempted_problem_ids:
            topic_map[top]['attempted'] += 1

    topic_progress = []
    for top_name, data in topic_map.items():
        pct = round((data['solved'] / data['total']) * 100, 1) if data['total'] > 0 else 0
        topic_progress.append({
            'topic': top_name,
            'total': data['total'],
            'solved': data['solved'],
            'attempted': data['attempted'],
            'percentage': pct
        })
    topic_progress.sort(key=lambda x: x['percentage'], reverse=True)

    # Recommended next problems (unsolved problems, starting with Easy/Medium)
    recommended_problems = [
        p for p in all_problems if p.id not in solved_problem_ids
    ][:5]

    # Recent submissions (last 8)
    recent_submissions = submissions[:8]

    # Placement readiness sync
    placement_profile = PlacementProfile.query.filter_by(student_id=student_id).first()

    return render_template(
        'coding_lab/dashboard.html',
        current_user=user,
        student=student,
        total_submissions=total_submissions,
        problems_attempted=problems_attempted_count,
        problems_solved=problems_solved_count,
        total_problems=total_problems_count,
        success_rate=success_rate,
        current_streak=current_streak,
        difficulty_stats=difficulty_stats,
        topic_progress=topic_progress,
        recommended_problems=recommended_problems,
        recent_submissions=recent_submissions,
        placement_profile=placement_profile
    )


# ============================================================================
# 2. CODING PRACTICE CATALOG (/student/coding-lab/practice)
# ============================================================================
@coding_lab_bp.route('/student/coding-lab/practice')
@login_required
def practice_catalog():
    """Browse, filter, and search practice coding problems."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    # Query parameters
    search = request.args.get('search', '').strip()
    topic_filter = request.args.get('topic', '').strip()
    difficulty_filter = request.args.get('difficulty', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = CodingProblem.query

    if search:
        query = query.filter(CodingProblem.title.ilike(f'%{search}%') | CodingProblem.description_markdown.ilike(f'%{search}%'))
    if topic_filter:
        query = query.filter_by(topic=topic_filter)
    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)

    all_matching = query.order_by(CodingProblem.id.asc()).all()

    # Get student solved and attempted sets
    user_submissions = CodingSubmission.query.filter_by(student_id=student_id).all()
    solved_ids = set(s.problem_id for s in user_submissions if s.status == 'Accepted')
    attempted_ids = set(s.problem_id for s in user_submissions if s.status != 'Accepted') - solved_ids

    # Assemble problems with user-specific status
    problem_items = []
    for p in all_matching:
        if p.id in solved_ids:
            p_status = 'Solved'
        elif p.id in attempted_ids:
            p_status = 'Attempted'
        else:
            p_status = 'Todo'

        if status_filter and status_filter != 'All' and p_status != status_filter:
            continue

        # Calculate acceptance rate for this problem
        p_subs = CodingSubmission.query.filter_by(problem_id=p.id).all()
        acc_rate = round((len([s for s in p_subs if s.status == 'Accepted']) / len(p_subs) * 100), 1) if p_subs else 100.0

        problem_items.append({
            'problem': p,
            'status': p_status,
            'acceptance_rate': acc_rate,
            'total_submissions': len(p_subs)
        })

    # Available topics for filter dropdown
    all_topics = db.session.query(CodingProblem.topic).distinct().all()
    topics_list = [t[0] for t in all_topics if t[0]]

    return render_template(
        'coding_lab/practice.html',
        current_user=user,
        student=student,
        problems=problem_items,
        topics=topics_list,
        current_search=search,
        current_topic=topic_filter,
        current_difficulty=difficulty_filter,
        current_status=status_filter,
        total_count=len(problem_items)
    )


# ============================================================================
# 3. INTERACTIVE 3-PANEL CODE EDITOR (/student/coding-lab/practice/<identifier>)
# ============================================================================
@coding_lab_bp.route('/student/coding-lab/practice/<identifier>')
@login_required
def editor_view(identifier):
    """Full 3-panel ByteXL-style Monaco online coding IDE."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    # Lookup problem by slug or ID
    problem = None
    if identifier.isdigit():
        problem = CodingProblem.query.get(int(identifier))
    if not problem:
        problem = CodingProblem.query.filter_by(slug=identifier).first()
    
    if not problem:
        flash(f"Problem '{identifier}' not found. Redirecting to practice catalog.", 'warning')
        return redirect(url_for('coding_lab.practice_catalog'))

    # Retrieve existing draft for current student
    draft = StudentCodeDraft.query.filter_by(
        student_id=student_id,
        problem_id=problem.id,
        language='python'
    ).first()

    initial_code = draft.code if draft and draft.code else problem.get_starter_code('python')

    # Retrieve student's submission history for this specific problem
    user_problem_submissions = CodingSubmission.query.filter_by(
        student_id=student_id,
        problem_id=problem.id
    ).order_by(CodingSubmission.submitted_at.desc()).limit(10).all()

    # Get adjacent problems for Next/Previous navigation
    all_problems = CodingProblem.query.order_by(CodingProblem.id.asc()).all()
    current_idx = next((i for i, p in enumerate(all_problems) if p.id == problem.id), 0)
    prev_problem = all_problems[current_idx - 1] if current_idx > 0 else None
    next_problem = all_problems[current_idx + 1] if current_idx < len(all_problems) - 1 else None

    # Available languages
    languages = get_available_languages()

    return render_template(
        'coding_lab/editor.html',
        current_user=user,
        student=student,
        problem=problem,
        initial_code=initial_code,
        public_test_cases=problem.get_public_test_cases(),
        user_submissions=user_problem_submissions,
        prev_problem=prev_problem,
        next_problem=next_problem,
        languages=languages,
        all_problems=all_problems
    )


# ============================================================================
# 4. SUBMISSIONS HISTORY (/student/coding-lab/submissions)
# ============================================================================
@coding_lab_bp.route('/student/coding-lab/submissions')
@login_required
def submissions_list():
    """View all past code submissions, results, and runtime analytics."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    submissions = CodingSubmission.query.filter_by(
        student_id=student_id
    ).order_by(CodingSubmission.submitted_at.desc()).all()

    return render_template(
        'coding_lab/submissions.html',
        current_user=user,
        student=student,
        submissions=submissions
    )


# ============================================================================
# 5. TOPIC MASTERY & PROGRESS (/student/coding-lab/progress)
# ============================================================================
@coding_lab_bp.route('/student/coding-lab/progress')
@login_required
def progress_view():
    """Deep-dive into student's coding mastery, topic coverage, and placement readiness."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    submissions = CodingSubmission.query.filter_by(student_id=student_id).all()
    all_problems = CodingProblem.query.all()

    solved_problem_ids = set(s.problem_id for s in submissions if s.status == 'Accepted')

    # Topic breakdown
    topics_breakdown = {}
    for p in all_problems:
        t = p.topic or 'General'
        if t not in topics_breakdown:
            topics_breakdown[t] = {'total': 0, 'solved': 0, 'points_total': 0, 'points_earned': 0}
        topics_breakdown[t]['total'] += 1
        topics_breakdown[t]['points_total'] += p.points
        if p.id in solved_problem_ids:
            topics_breakdown[t]['solved'] += 1
            topics_breakdown[t]['points_earned'] += p.points

    topic_metrics = []
    for t_name, data in topics_breakdown.items():
        pct = round((data['solved'] / max(1, data['total'])) * 100, 1)
        topic_metrics.append({
            'name': t_name,
            'total': data['total'],
            'solved': data['solved'],
            'points_earned': data['points_earned'],
            'points_total': data['points_total'],
            'percentage': pct
        })
    topic_metrics.sort(key=lambda x: x['percentage'], reverse=True)

    # Placement Profile alignment
    placement_profile = PlacementProfile.query.filter_by(student_id=student_id).first()

    return render_template(
        'coding_lab/progress.html',
        current_user=user,
        student=student,
        topic_metrics=topic_metrics,
        solved_count=len(solved_problem_ids),
        total_count=len(all_problems),
        total_submissions=len(submissions),
        placement_profile=placement_profile
    )


# ============================================================================
# API ENDPOINTS: CODE EXECUTION, SUBMISSION & DRAFTS
# ============================================================================

@coding_lab_bp.route('/api/coding/run', methods=['POST'])
@login_required
def api_run_code():
    """
    Safely execute student code against custom standard input.
    Subprocess sandbox, no Flask-thread execution.
    """
    data = request.get_json() or {}
    code = data.get('code', '')
    language = data.get('language', 'python')
    custom_input = data.get('custom_input', '')
    time_limit = float(data.get('time_limit_sec', 3.0))

    if not code or not code.strip():
        return jsonify({
            'success': False,
            'error': 'No code submitted to run.'
        }), 400

    result = run_custom_code(
        code=code,
        language=language,
        custom_input=custom_input,
        time_limit_sec=min(5.0, max(1.0, time_limit))
    )

    return jsonify({
        'success': True,
        'status': result['status'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'execution_time_ms': result['execution_time_ms'],
        'timed_out': result.get('timed_out', False),
        'exit_code': result.get('exit_code', 0)
    })


@coding_lab_bp.route('/api/coding/submit', methods=['POST'])
@login_required
def api_submit_code():
    """
    Evaluate code against all test cases (public + hidden) securely.
    Persists submission in database and updates student placement readiness.
    """
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    data = request.get_json() or {}
    problem_id = data.get('problem_id')
    code = data.get('code', '')
    language = data.get('language', 'python')

    if not problem_id:
        return jsonify({'success': False, 'error': 'Problem ID is required.'}), 400

    problem = CodingProblem.query.get(int(problem_id))
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found.'}), 404

    if not code or not code.strip():
        return jsonify({'success': False, 'error': 'Cannot submit empty code.'}), 400

    # Evaluate against backend test cases
    test_cases = problem.get_test_cases()
    evaluation = evaluate_submission(
        code=code,
        language=language,
        test_cases=test_cases,
        time_limit_sec=problem.time_limit_sec,
        points_total=problem.points
    )

    # Record submission in DB
    submission = CodingSubmission(
        student_id=student_id,
        problem_id=problem.id,
        language=language,
        code=code,
        status=evaluation['status'],
        passed_test_cases=evaluation['passed_test_cases'],
        total_test_cases=evaluation['total_test_cases'],
        score=evaluation['score'],
        execution_time_ms=evaluation['execution_time_ms'],
        error_message=evaluation.get('error_message', '')
    )
    db.session.add(submission)

    # Also update or save student draft
    draft = StudentCodeDraft.query.filter_by(
        student_id=student_id,
        problem_id=problem.id,
        language=language
    ).first()
    if draft:
        draft.code = code
        draft.updated_at = datetime.utcnow()
    else:
        draft = StudentCodeDraft(
            student_id=student_id,
            problem_id=problem.id,
            language=language,
            code=code
        )
        db.session.add(draft)

    db.session.commit()

    # Sync placement readiness index
    _sync_placement_coding_score(student_id)

    return jsonify({
        'success': True,
        'submission_id': submission.id,
        'status': evaluation['status'],
        'passed_test_cases': evaluation['passed_test_cases'],
        'total_test_cases': evaluation['total_test_cases'],
        'score': evaluation['score'],
        'points_max': problem.points,
        'execution_time_ms': evaluation['execution_time_ms'],
        'test_results': evaluation['test_results'],
        'error_message': evaluation.get('error_message', ''),
        'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
    })


@coding_lab_bp.route('/api/coding/draft/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def api_draft(problem_id):
    """Save or retrieve a student's private code draft for a given problem."""
    user, student = _get_student_context()
    student_id = student.student_id if student else (user.student_id or 'STU2024001')

    problem = CodingProblem.query.get(problem_id)
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found.'}), 404

    language = request.args.get('language', 'python') if request.method == 'GET' else (request.get_json() or {}).get('language', 'python')

    if request.method == 'POST':
        data = request.get_json() or {}
        code = data.get('code', '')
        
        draft = StudentCodeDraft.query.filter_by(
            student_id=student_id,
            problem_id=problem_id,
            language=language
        ).first()

        if draft:
            draft.code = code
            draft.updated_at = datetime.utcnow()
        else:
            draft = StudentCodeDraft(
                student_id=student_id,
                problem_id=problem_id,
                language=language,
                code=code
            )
            db.session.add(draft)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Draft saved successfully.',
            'updated_at': draft.updated_at.strftime('%H:%M:%S')
        })

    # GET request
    draft = StudentCodeDraft.query.filter_by(
        student_id=student_id,
        problem_id=problem_id,
        language=language
    ).first()

    code_content = draft.code if draft else problem.get_starter_code(language)
    return jsonify({
        'success': True,
        'code': code_content,
        'is_saved_draft': draft is not None,
        'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M:%S') if draft else None
    })


@coding_lab_bp.route('/api/coding/languages', methods=['GET'])
def api_languages():
    """Get list of supported programming languages and configuration status."""
    return jsonify({
        'success': True,
        'languages': get_available_languages()
    })
