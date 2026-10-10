"""
Automated Test Suite for Student Personal Workspace, Normal Editor,
Saved Files, File Versioning, and Coding History.
"""

import io
import pytest
from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.student_files import StudentFile, StudentFileVersion, StudentWorkspaceSetting
from backend.models.coding import CodingProblem, CodingSubmission


@pytest.fixture
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
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
# 1. Page Access & Routing Tests
# ============================================================================

def test_normal_editor_requires_auth(client):
    res = client.get('/student/editor')
    assert res.status_code == 302
    assert '/student/login' in res.headers['Location']


def test_normal_editor_renders_for_student(auth_student_client):
    res = auth_student_client.get('/student/editor')
    assert res.status_code == 302
    assert '/student/coding-lab' in res.headers['Location']


def test_saved_files_renders_for_student(auth_student_client):
    res = auth_student_client.get('/student/saved-files')
    assert res.status_code == 302
    assert '/student/coding-lab' in res.headers['Location']


def test_coding_history_renders_for_student(auth_student_client):
    res = auth_student_client.get('/student/coding-history')
    assert res.status_code == 200
    assert b'My Coding History' in res.data


def test_student_progress_redirect(auth_student_client):
    res = auth_student_client.get('/student/progress')
    assert res.status_code == 302
    assert '/student/coding-lab/progress' in res.headers['Location']


# ============================================================================
# 2. File CRUD & Operations APIs
# ============================================================================

import uuid

def test_file_create_and_read(auth_student_client, test_app):
    # Create file with unique name
    unique_fname = f"algo_{uuid.uuid4().hex[:8]}.py"
    res = auth_student_client.post('/api/student/files', json={
        'filename': unique_fname,
        'content': 'print("Hello Algorithms")'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    file_id = data['file']['id']
    assert data['file']['filename'] == unique_fname


    # Read file
    res_get = auth_student_client.get(f'/api/student/files/{file_id}')

    assert res_get.status_code == 200
    get_data = res_get.get_json()
    assert get_data['success'] is True
    assert get_data['file']['content'] == 'print("Hello Algorithms")'
    assert len(get_data['versions']) >= 1


def test_file_update_and_version_recording(auth_student_client, test_app):
    with test_app.app_context():
        f = StudentFile(student_id='STU2024001', filename='test_ver.py', content='v1 content')
        db.session.add(f)
        db.session.commit()
        f.update_content('v1 content', summary='Initial', create_version=True)
        db.session.commit()
        fid = f.id

    # Update with manual save
    res = auth_student_client.put(f'/api/student/files/{fid}', json={
        'content': 'v2 content modified',
        'summary': 'Second revision',
        'create_version': True
    })
    assert res.status_code == 200

    # Verify versions
    res_ver = auth_student_client.get(f'/api/student/files/{fid}/versions')
    assert res_ver.status_code == 200
    v_data = res_ver.get_json()
    assert len(v_data['versions']) >= 2
    assert v_data['versions'][0]['version_number'] == 2


def test_file_version_restore(auth_student_client, test_app):
    with test_app.app_context():
        f = StudentFile(student_id='STU2024001', filename='restore_test.py', content='first edition')
        db.session.add(f)
        db.session.commit()
        v1 = f.update_content('first edition', summary='v1', create_version=True)
        db.session.commit()
        v1_id = v1.id

        v2 = f.update_content('second edition with breaking change', summary='v2', create_version=True)
        db.session.commit()
        fid = f.id

    # Restore v1
    res = auth_student_client.post(f'/api/student/files/{fid}/versions/{v1_id}/restore')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['file']['content'] == 'first edition'
    # New version should have been created
    assert data['new_version_number'] == 3


def test_file_rename_and_duplicate(auth_student_client, test_app):
    with test_app.app_context():
        f = StudentFile(student_id='STU2024001', filename='orig.js', content='console.log(1)')
        db.session.add(f)
        db.session.commit()
        fid = f.id

    # Rename
    res_rename = auth_student_client.patch(f'/api/student/files/{fid}/rename', json={
        'new_filename': 'renamed_app.js'
    })
    assert res_rename.status_code == 200
    assert res_rename.get_json()['file']['filename'] == 'renamed_app.js'

    # Duplicate
    res_dup = auth_student_client.post(f'/api/student/files/{fid}/duplicate')
    assert res_dup.status_code == 200
    dup_data = res_dup.get_json()
    assert dup_data['success'] is True
    assert dup_data['file']['filename'] == 'renamed_app_copy.js'


def test_file_download(auth_student_client, test_app):
    with test_app.app_context():
        f = StudentFile(student_id='STU2024001', filename='download_me.txt', content='Sample Content To Download')
        db.session.add(f)
        db.session.commit()
        fid = f.id

    res = auth_student_client.get(f'/api/student/files/{fid}/download')
    assert res.status_code == 200
    assert b'Sample Content To Download' in res.data
    assert 'attachment' in res.headers['Content-Disposition']


def test_file_upload(auth_student_client):
    file_bytes = io.BytesIO(b'def uploaded_func(): return 42')
    res = auth_student_client.post('/api/student/files/upload', data={
        'file': (file_bytes, 'uploaded_script.py')
    }, content_type='multipart/form-data')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['file']['filename'] == 'uploaded_script.py'


def test_file_delete(auth_student_client, test_app):
    with test_app.app_context():
        f = StudentFile(student_id='STU2024001', filename='to_delete.py', content='bye')
        db.session.add(f)
        db.session.commit()
        fid = f.id

    res = auth_student_client.delete(f'/api/student/files/{fid}')
    assert res.status_code == 200

    # Should no longer be retrievable
    res_get = auth_student_client.get(f'/api/student/files/{fid}')
    assert res_get.status_code == 404


# ============================================================================
# 3. Student Isolation & Cross-Student Security Tests
# ============================================================================

def test_cross_student_file_access_denied(test_app, client):
    with test_app.app_context():
        f_stu1 = StudentFile(student_id='STU2024001', filename='secret_stu1.py', content='stu1 secrets')
        db.session.add(f_stu1)
        db.session.commit()
        stu1_file_id = f_stu1.id

    # Authenticate as Student 2
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['role'] = 'Student'
        sess['username'] = 'stu_priya'
        sess['student_id'] = 'STU2024002'

    # Student 2 cannot read Student 1's file
    res_get = client.get(f'/api/student/files/{stu1_file_id}')
    assert res_get.status_code == 404

    # Student 2 cannot update Student 1's file
    res_put = client.put(f'/api/student/files/{stu1_file_id}', json={'content': 'hacked'})
    assert res_put.status_code == 404

    # Student 2 cannot delete Student 1's file
    res_del = client.delete(f'/api/student/files/{stu1_file_id}')
    assert res_del.status_code == 404

    # Student 2 cannot download Student 1's file
    res_down = client.get(f'/api/student/files/{stu1_file_id}/download')
    assert res_down.status_code == 404


# ============================================================================
# 4. Workspace Settings Persistence Tests
# ============================================================================

def test_workspace_settings_update_and_restore(auth_student_client):
    res_set = auth_student_client.post('/api/student/workspace/settings', json={
        'theme': 'vs',
        'font_size': 16
    })
    assert res_set.status_code == 200
    assert res_set.get_json()['settings']['theme'] == 'vs'
    assert res_set.get_json()['settings']['font_size'] == 16

    res_get = auth_student_client.get('/api/student/workspace/settings')
    assert res_get.status_code == 200
    assert res_get.get_json()['settings']['theme'] == 'vs'
    assert res_get.get_json()['settings']['font_size'] == 16
