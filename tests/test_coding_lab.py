"""
Automated Test Suite for Coding Lab and Sandboxed Code Execution Service.
Tests authentication, permissions, code execution timeouts, draft persistence,
hidden test cases confidentiality, submission recording, and placement integration.
"""

import os
import json
import pytest
from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.coding import CodingProblem, StudentCodeDraft, CodingSubmission
from backend.models.placement import PlacementProfile
from backend.services.code_executor import run_custom_code, evaluate_submission


@pytest.fixture
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        yield app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def auth_student_client(test_app, client):
    """Log in as student STU2024001."""
    with test_app.app_context():
        stu_user = User.query.filter_by(username='stu_rahul').first()
        if not stu_user:
            stu = Student.query.filter_by(student_id='STU2024001').first()
            if not stu:
                stu = Student(
                    student_id='STU2024001',
                    first_name='Rahul',
                    last_name='Sharma',
                    email='stu_rahul@campus.edu',
                    department='Computer Science & Engineering',
                    academic_year=2,
                    semester=3
                )
                db.session.add(stu)
            stu_user = User(
                username='stu_rahul',
                email='stu_rahul@campus.edu',
                full_name='Rahul Sharma',
                role='Student',
                student_id='STU2024001'
            )
            stu_user.set_password('Student@123')
            db.session.add(stu_user)
            db.session.commit()
        uid = stu_user.id
        uname = stu_user.username
        sid = stu_user.student_id

    with client.session_transaction() as sess:
        sess['user_id'] = uid
        sess['role'] = 'Student'
        sess['username'] = uname
        sess['student_id'] = sid
    return client


# ============================================================================
# 1. Code Execution Sandboxing Tests
# ============================================================================

def test_code_executor_run_simple_python(test_app):
    code = "import sys\nline = sys.stdin.read().strip()\nprint(f'Hello {line}')\n"
    res = run_custom_code(code, 'python', 'World', 3.0)
    assert res['status'] == 'Success'
    assert res['exit_code'] == 0
    assert 'Hello World' in res['stdout']
    assert res['timed_out'] is False


def test_code_executor_timeout_protection(test_app):
    code = "import time\nwhile True:\n    time.sleep(0.1)\n"
    res = run_custom_code(code, 'python', '', 1.0)
    assert res['status'] == 'Time Limit Exceeded'
    assert res['timed_out'] is True


def test_code_executor_syntax_error(test_app):
    code = "def broken(:\n  print('error')"
    res = run_custom_code(code, 'python', '', 2.0)
    assert res['status'] == 'Compilation Error'
    assert res['exit_code'] != 0


def test_code_executor_evaluation_with_hidden_cases(test_app):
    code = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n"
    test_cases = [
        {"input": "2 3\n", "expected_output": "5", "is_hidden": False},
        {"input": "10 20\n", "expected_output": "30", "is_hidden": True},
    ]
    eval_res = evaluate_submission(code, 'python', test_cases, 2.0, points_total=20)
    assert eval_res['status'] == 'Accepted'
    assert eval_res['passed_test_cases'] == 2
    assert eval_res['total_test_cases'] == 2
    assert eval_res['score'] == 20.0
    
    # Check hidden case confidentiality
    hidden_case = next(c for c in eval_res['test_results'] if c['is_hidden'])
    assert hidden_case['input'] == '[Hidden Test Case]'
    assert hidden_case['expected_output'] == '[Hidden Test Case]'


def test_code_executor_wrong_answer_handling(test_app):
    code = "import sys\nprint('wrong answer')\n"
    test_cases = [
        {"input": "2 3\n", "expected_output": "5", "is_hidden": False},
    ]
    eval_res = evaluate_submission(code, 'python', test_cases, 2.0, points_total=10)
    assert eval_res['status'] == 'Wrong Answer'
    assert eval_res['passed_test_cases'] == 0


# ============================================================================
# 2. Authentication & Authorization Tests
# ============================================================================

def test_unauthenticated_access_redirects(client):
    res = client.get('/student/coding-lab')
    assert res.status_code == 302 # Redirect to student login
    assert '/student/login' in res.headers['Location']


def test_authenticated_student_access_dashboard(auth_student_client):
    res = auth_student_client.get('/student/coding-lab')
    assert res.status_code == 200
    assert b'Coding Lab' in res.data
    assert b'Problems Solved' in res.data


def test_authenticated_student_access_practice_catalog(auth_student_client):
    res = auth_student_client.get('/student/coding-lab/practice')
    assert res.status_code == 200
    assert b'Coding Practice Library' in res.data


def test_authenticated_student_access_submissions(auth_student_client):
    res = auth_student_client.get('/student/coding-lab/submissions')
    assert res.status_code == 200
    assert b'My Coding Submissions' in res.data


def test_authenticated_student_access_progress(auth_student_client):
    res = auth_student_client.get('/student/coding-lab/progress')
    assert res.status_code == 200
    assert b'Topic Mastery' in res.data


# ============================================================================
# 3. Problem Retrieval & Editor Tests
# ============================================================================

def test_editor_view_valid_problem(auth_student_client, test_app):
    with test_app.app_context():
        problem = CodingProblem.query.first()
        assert problem is not None
        slug = problem.slug

    res = auth_student_client.get(f'/student/coding-lab/practice/{slug}')
    assert res.status_code == 200
    assert b'Run Code' in res.data
    assert b'Submit Solution' in res.data


def test_editor_view_invalid_problem_redirects(auth_student_client):
    res = auth_student_client.get('/student/coding-lab/practice/nonexistent-slug-xyz')
    assert res.status_code == 302
    assert '/student/coding-lab/practice' in res.headers['Location']


# ============================================================================
# 4. API Endpoints: Run, Submit, Drafts & Placement Integration
# ============================================================================

def test_api_run_code(auth_student_client):
    res = auth_student_client.post('/api/coding/run', json={
        'code': "import sys\nprint('Test Output Runner')",
        'language': 'python',
        'custom_input': ''
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'Test Output Runner' in data['stdout']


def test_api_submit_code_and_persistence(auth_student_client, test_app):
    with test_app.app_context():
        prob = CodingProblem.query.filter_by(slug='two-sum-problem').first()
        assert prob is not None
        prob_id = prob.id

    # Submit correct solution
    solution_code = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n"
    res = auth_student_client.post('/api/coding/submit', json={
        'problem_id': prob_id,
        'code': solution_code,
        'language': 'python'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['status'] == 'Accepted'
    assert data['passed_test_cases'] == data['total_test_cases']
    assert data['score'] == 10.0

    # Verify persistence in database
    with test_app.app_context():
        submission = CodingSubmission.query.get(data['submission_id'])
        assert submission is not None
        assert submission.status == 'Accepted'
        assert submission.student_id == 'STU2024001'

        # Check draft was also automatically updated
        draft = StudentCodeDraft.query.filter_by(
            student_id='STU2024001',
            problem_id=prob_id
        ).first()
        assert draft is not None
        assert draft.code == solution_code

        # Check placement profile coding score updated
        placement_profile = PlacementProfile.query.filter_by(student_id='STU2024001').first()
        assert placement_profile is not None
        assert placement_profile.coding_score > 0.0


def test_draft_save_and_retrieve_isolation(test_app, client):
    with test_app.app_context():
        prob = CodingProblem.query.first()
        prob_id = prob.id

        u1 = User.query.filter_by(student_id='STU2024001').first()
        if not u1:
            u1 = User(username='stu1', email='stu1@campus.edu', full_name='Student 1', role='Student', student_id='STU2024001')
            u1.set_password('Student@123')
            db.session.add(u1)
        u2 = User.query.filter_by(student_id='STU2024002').first()
        if not u2:
            u2 = User(username='stu2', email='stu2@campus.edu', full_name='Student 2', role='Student', student_id='STU2024002')
            u2.set_password('Student@123')
            db.session.add(u2)
        db.session.commit()
        u1_id = u1.id
        u2_id = u2.id

    # Save draft for Student 1
    with client.session_transaction() as sess:
        sess['user_id'] = u1_id
        sess['role'] = 'Student'
        sess['student_id'] = 'STU2024001'

    res = client.post(f'/api/coding/draft/{prob_id}', json={
        'code': '# Code from Student 1',
        'language': 'python'
    })
    assert res.status_code == 200

    # Retrieve draft for Student 1
    res_get = client.get(f'/api/coding/draft/{prob_id}')
    assert res_get.get_json()['code'] == '# Code from Student 1'

    # Switch session to Student 2
    with client.session_transaction() as sess:
        sess['user_id'] = u2_id
        sess['role'] = 'Student'
        sess['student_id'] = 'STU2024002'

    # Student 2 should NOT see Student 1's draft
    res_get2 = client.get(f'/api/coding/draft/{prob_id}')
    assert res_get2.get_json()['code'] != '# Code from Student 1'
