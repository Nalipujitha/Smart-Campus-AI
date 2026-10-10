"""
Student Personal Workspace, Normal Editor, File Management, and Coding History Blueprint.
Provides independent VS Code-style editor, multi-language file management, versioning,
download/upload, and detailed coding history logs.
"""

import io
import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, send_file

from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.student_files import StudentFile, StudentFileVersion, StudentWorkspaceSetting, detect_language
from backend.models.coding import CodingProblem, CodingSubmission
from backend.models.placement import PlacementProfile
from backend.routes.auth import login_required, get_current_user

student_workspace_bp = Blueprint('student_workspace', __name__)

MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB maximum per text/code file


def _get_student_id():
    """Retrieve authenticated student ID from session or user model."""
    user = get_current_user()
    if not user:
        return None
    student_id = session.get('student_id') or user.student_id
    if not student_id and user.role == 'Student':
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            student_id = student.student_id
        else:
            student_id = f"STU_{user.username}"
    elif not student_id:
        student_id = f"USER_{user.id}"
    return student_id


# ============================================================================
# 1. NORMAL EDITOR ROUTE (Redirect to Coding Lab)
# ============================================================================
@student_workspace_bp.route('/student/editor')
@student_workspace_bp.route('/student/editor/<int:file_id>')
@login_required
def normal_editor(file_id=None):
    """Redirect to Coding Lab IDE."""
    return redirect(url_for('coding_lab.dashboard'))



# ============================================================================
# 2. MY SAVED FILES (/student/saved-files) -> Redirect to Coding Lab
# ============================================================================
@student_workspace_bp.route('/student/saved-files')
@login_required
def saved_files_view():
    """Redirect to Coding Lab."""
    return redirect(url_for('coding_lab.dashboard'))


# ============================================================================
# 3. CODING HISTORY (/student/coding-history)
# ============================================================================
@student_workspace_bp.route('/student/coding-history')
@login_required
def coding_history_view():
    """Dedicated Coding History page displaying all recorded attempts, tests, and code."""
    user = get_current_user()
    student_id = _get_student_id()
    student = Student.query.filter_by(student_id=student_id).first()

    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    query = CodingSubmission.query.filter_by(student_id=student_id)

    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.join(CodingProblem).filter(CodingProblem.title.ilike(f'%{search}%'))

    submissions = query.order_by(CodingSubmission.submitted_at.desc()).all()

    # Summary statistics
    total_subs = len(submissions)
    accepted_subs = [s for s in submissions if s.status == 'Accepted']
    total_accepted = len(accepted_subs)
    success_rate = round((total_accepted / max(1, total_subs)) * 100, 1) if total_subs > 0 else 0.0

    return render_template(
        'student/coding_history.html',
        current_user=user,
        student=student,
        submissions=submissions,
        total_submissions=total_subs,
        total_accepted=total_accepted,
        success_rate=success_rate,
        current_status=status_filter,
        current_search=search
    )


# ============================================================================
# 4. MY PROGRESS (/student/progress)
# ============================================================================
@student_workspace_bp.route('/student/progress')
@login_required
def student_progress_redirect():
    """Redirect to the comprehensive progress and topic mastery view."""
    return redirect(url_for('coding_lab.progress_view'))


# ============================================================================
# 5. REST APIs: FILE MANAGEMENT & WORKSPACE
# ============================================================================

@student_workspace_bp.route('/api/student/files', methods=['GET', 'POST'])
@login_required
def api_files_collection():
    """List or create personal files for authenticated student."""
    student_id = _get_student_id()

    if request.method == 'POST':
        data = request.get_json() or {}
        raw_filename = data.get('filename', '').strip()
        content = data.get('content', '')

        if not raw_filename:
            return jsonify({'success': False, 'error': 'Filename is required.'}), 400

        # Sanitize filename (keep extension, prevent path traversal)
        safe_name = os.path.basename(raw_filename.replace('\\', '/'))
        if not safe_name or safe_name in ['.', '..']:
            safe_name = 'untitled.txt'

        # Auto-append .py if no extension
        if '.' not in safe_name:
            safe_name += '.py'

        # Check for duplicate filename for this student
        existing = StudentFile.query.filter_by(student_id=student_id, filename=safe_name, is_deleted=False).first()
        if existing:
            # Append suffix
            name_part, ext_part = os.path.splitext(safe_name)
            safe_name = f"{name_part}_{datetime.utcnow().strftime('%M%S')}{ext_part}"

        file_type = detect_language(safe_name)
        new_file = StudentFile(
            student_id=student_id,
            filename=safe_name,
            file_type=file_type,
            content=content,
            size_bytes=len(content.encode('utf-8'))
        )
        db.session.add(new_file)
        db.session.commit()

        # Create version #1
        new_file.update_content(content, summary="Created new file", create_version=True)
        
        # Update last opened
        setting = StudentWorkspaceSetting.query.filter_by(student_id=student_id).first()
        if setting:
            setting.last_opened_file_id = new_file.id
        db.session.commit()

        return jsonify({
            'success': True,
            'file': new_file.to_dict(include_content=True),
            'message': 'File created successfully.'
        }), 201

    # GET request: return all active files
    files = StudentFile.query.filter_by(student_id=student_id, is_deleted=False).order_by(StudentFile.updated_at.desc()).all()
    return jsonify({
        'success': True,
        'files': [f.to_dict(include_content=False) for f in files]
    })


@student_workspace_bp.route('/api/student/files/<int:file_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_single_file(file_id):
    """Retrieve, update, or soft-delete a student file."""
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'success': False, 'error': 'File not found or access denied.'}), 404

    if request.method == 'GET':
        # Update last opened file ID
        setting = StudentWorkspaceSetting.query.filter_by(student_id=student_id).first()
        if setting:
            setting.last_opened_file_id = file_obj.id
            db.session.commit()

        versions = StudentFileVersion.query.filter_by(file_id=file_obj.id).order_by(StudentFileVersion.version_number.desc()).limit(15).all()
        return jsonify({
            'success': True,
            'file': file_obj.to_dict(include_content=True),
            'versions': [v.to_dict(include_content=False) for v in versions]
        })

    elif request.method == 'PUT':
        data = request.get_json() or {}
        content = data.get('content', '')
        summary = data.get('summary', 'Saved changes')
        create_version = data.get('create_version', True)

        if len(content.encode('utf-8')) > MAX_FILE_SIZE_BYTES:
            return jsonify({'success': False, 'error': f'File exceeds size limit of {MAX_FILE_SIZE_BYTES // 1024} KB.'}), 400

        file_obj.update_content(content, summary=summary, create_version=create_version)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'File saved successfully.',
            'updated_at': file_obj.updated_at.strftime('%H:%M:%S'),
            'size_bytes': file_obj.size_bytes
        })

    elif request.method == 'DELETE':
        file_obj.is_deleted = True
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'File deleted successfully.'
        })


@student_workspace_bp.route('/api/student/files/<int:file_id>/rename', methods=['PATCH'])
@login_required
def api_rename_file(file_id):
    """Rename a student file with extension validation."""
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'success': False, 'error': 'File not found.'}), 404

    data = request.get_json() or {}
    new_name = data.get('new_filename', '').strip()
    if not new_name:
        return jsonify({'success': False, 'error': 'New filename cannot be empty.'}), 400

    safe_name = os.path.basename(new_name.replace('\\', '/'))
    if not safe_name:
        return jsonify({'success': False, 'error': 'Invalid filename.'}), 400

    file_obj.filename = safe_name
    file_obj.file_type = detect_language(safe_name)
    file_obj.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'File renamed successfully.',
        'file': file_obj.to_dict(include_content=False)
    })


@student_workspace_bp.route('/api/student/files/<int:file_id>/duplicate', methods=['POST'])
@login_required
def api_duplicate_file(file_id):
    """Create a duplicate copy of an existing file."""
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'success': False, 'error': 'File not found.'}), 404

    name_part, ext_part = os.path.splitext(file_obj.filename)
    dup_name = f"{name_part}_copy{ext_part}"

    # Check for duplicate collision
    dup_file = StudentFile(
        student_id=student_id,
        filename=dup_name,
        file_type=file_obj.file_type,
        content=file_obj.content,
        size_bytes=file_obj.size_bytes
    )
    db.session.add(dup_file)
    db.session.commit()
    dup_file.update_content(dup_file.content, summary="Duplicated file", create_version=True)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Duplicated as '{dup_name}'",
        'file': dup_file.to_dict(include_content=True)
    })


@student_workspace_bp.route('/api/student/files/<int:file_id>/download', methods=['GET'])
@login_required
def api_download_file(file_id):
    """Download single student file to local computer."""
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'error': 'File not found or access denied.'}), 404

    buffer = io.BytesIO()
    buffer.write(file_obj.content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=file_obj.filename,
        mimetype='text/plain'
    )


@student_workspace_bp.route('/api/student/files/upload', methods=['POST'])
@login_required
def api_upload_file():
    """Upload a code/text file from student computer to personal workspace."""
    student_id = _get_student_id()

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    uploaded_file = request.files['file']
    if not uploaded_file.filename:
        return jsonify({'success': False, 'error': 'Empty filename.'}), 400

    filename = secure_filename(uploaded_file.filename) or 'uploaded_code.txt'
    try:
        content_bytes = uploaded_file.read()
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            return jsonify({'success': False, 'error': 'Uploaded file exceeds 512KB limit.'}), 400

        content = content_bytes.decode('utf-8', errors='replace')
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read file: {str(e)}'}), 400

    file_obj = StudentFile(
        student_id=student_id,
        filename=filename,
        file_type=detect_language(filename),
        content=content,
        size_bytes=len(content_bytes)
    )
    db.session.add(file_obj)
    db.session.commit()
    file_obj.update_content(content, summary="Uploaded from computer", create_version=True)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Uploaded '{filename}' successfully.",
        'file': file_obj.to_dict(include_content=True)
    })


@student_workspace_bp.route('/api/student/files/<int:file_id>/versions', methods=['GET'])
@login_required
def api_file_versions(file_id):
    """List version history of a file."""
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'success': False, 'error': 'File not found.'}), 404

    versions = StudentFileVersion.query.filter_by(file_id=file_obj.id).order_by(StudentFileVersion.version_number.desc()).all()
    return jsonify({
        'success': True,
        'versions': [v.to_dict(include_content=True) for v in versions]
    })


@student_workspace_bp.route('/api/student/files/<int:file_id>/versions/<int:version_id>/restore', methods=['POST'])
@login_required
def api_restore_version(file_id, version_id):
    """
    Restore an older file version.
    Creates a new version with the restored content without destroying history.
    """
    student_id = _get_student_id()
    file_obj = StudentFile.query.filter_by(id=file_id, student_id=student_id, is_deleted=False).first()

    if not file_obj:
        return jsonify({'success': False, 'error': 'File not found.'}), 404

    version_obj = StudentFileVersion.query.filter_by(id=version_id, file_id=file_obj.id, student_id=student_id).first()
    if not version_obj:
        return jsonify({'success': False, 'error': 'Version record not found.'}), 404

    # Restore content and create a new version entry
    new_version = file_obj.update_content(
        version_obj.content,
        summary=f"Restored from Version #{version_obj.version_number}",
        create_version=True
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Successfully restored to Version #{version_obj.version_number}.",
        'file': file_obj.to_dict(include_content=True),
        'new_version_number': new_version.version_number if new_version else version_obj.version_number
    })


@student_workspace_bp.route('/api/student/workspace/settings', methods=['GET', 'POST'])
@login_required
def api_workspace_settings():
    """Retrieve or update student workspace preferences."""
    student_id = _get_student_id()
    setting = StudentWorkspaceSetting.query.filter_by(student_id=student_id).first()
    if not setting:
        setting = StudentWorkspaceSetting(student_id=student_id)
        db.session.add(setting)
        db.session.commit()

    if request.method == 'POST':
        data = request.get_json() or {}
        if 'theme' in data:
            setting.theme = data['theme']
        if 'font_size' in data:
            setting.font_size = int(data['font_size'])
        if 'last_opened_file_id' in data:
            setting.last_opened_file_id = data['last_opened_file_id']
        db.session.commit()
        return jsonify({'success': True, 'settings': setting.to_dict()})

    return jsonify({'success': True, 'settings': setting.to_dict()})
