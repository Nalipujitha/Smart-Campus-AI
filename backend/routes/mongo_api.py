from flask import Blueprint, request, jsonify, session
from backend.db_mongo import mongo_manager, get_mongo_db
from backend.services.mongo_service import MongoStudentService
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.models.student import Student

mongo_api_bp = Blueprint('mongo_api', __name__, url_prefix='/api/v1/mongo')

@mongo_api_bp.route('/status', methods=['GET'])
def get_status():
    """
    Returns live MongoDB Atlas connection status and collection statistics.
    """
    status = mongo_manager.get_status()
    status_code = 200 if status.get('connected') else 503
    return jsonify({
        'status': 'success' if status.get('connected') else 'disconnected',
        'atlas': status
    }), status_code


@mongo_api_bp.route('/sync', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def sync_database():
    """
    Triggers full synchronization of relational student profiles to MongoDB Atlas.
    """
    result = MongoStudentService.sync_all_database_to_mongo()
    code = 200 if result.get('success') else 500
    return jsonify(result), code


@mongo_api_bp.route('/students', methods=['GET'])
@login_required
def list_students():
    """
    Retrieves paginated student profiles directly from MongoDB Atlas.
    """
    user = get_current_user()
    if user.role == 'Student':
        # Student role can only query their own record
        doc = MongoStudentService.get_unified_student_document(user.student_id)
        if not doc:
            return jsonify({'items': [], 'total': 0, 'page': 1, 'per_page': 15, 'pages': 0}), 200
        return jsonify({'items': [doc], 'total': 1, 'page': 1, 'per_page': 15, 'pages': 1}), 200

    filters = {
        'department': request.args.get('department'),
        'academic_year': request.args.get('academic_year'),
        'semester': request.args.get('semester'),
        'status': request.args.get('status'),
        'search': request.args.get('search')
    }
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)

    result = MongoStudentService.list_students(filter_params=filters, page=page, per_page=per_page)
    return jsonify(result), 200


@mongo_api_bp.route('/students/<student_id>', methods=['GET'])
@login_required
def get_student(student_id):
    """
    Retrieves full unified student dossier from MongoDB Atlas.
    Enforces authorization: Student can only view their own profile.
    """
    user = get_current_user()
    stu_id = str(student_id).strip().upper()

    if user.role == 'Student' and user.student_id != stu_id:
        return jsonify({'error': 'Unauthorized: Access to other student profiles is prohibited.'}), 403

    doc = MongoStudentService.get_unified_student_document(stu_id)
    if not doc:
        # Fallback check if student exists in relational DB and sync on-the-fly
        student_obj = Student.query.filter_by(student_id=stu_id).first()
        if student_obj and MongoStudentService.is_connected():
            MongoStudentService.sync_student_to_mongo(student_obj)
            doc = MongoStudentService.get_unified_student_document(stu_id)

    if not doc:
        return jsonify({'error': f"Student '{stu_id}' not found in MongoDB Atlas"}), 404

    return jsonify({'status': 'success', 'data': doc}), 200


@mongo_api_bp.route('/students', methods=['POST'])
@login_required
@roles_required('Admin')
def create_student():
    """
    Creates a new student document in MongoDB Atlas.
    """
    data = request.get_json() or {}
    success, err, created_doc = MongoStudentService.create_or_update_student(data)
    if not success:
        return jsonify({'error': err or 'Failed to create student'}), 400

    return jsonify({
        'status': 'success',
        'message': f"Student {created_doc.get('student_id')} created in MongoDB Atlas",
        'data': created_doc
    }), 201


@mongo_api_bp.route('/students/<student_id>', methods=['PUT', 'PATCH'])
@login_required
def update_student(student_id):
    """
    Updates a student document in MongoDB Atlas.
    """
    user = get_current_user()
    stu_id = str(student_id).strip().upper()

    if user.role == 'Student' and user.student_id != stu_id:
        return jsonify({'error': 'Unauthorized: You can only update your own record.'}), 403
    if user.role not in ['Admin', 'Faculty', 'Student']:
        return jsonify({'error': 'Forbidden access'}), 403

    data = request.get_json() or {}
    data['student_id'] = stu_id

    success, err, updated_doc = MongoStudentService.create_or_update_student(data)
    if not success:
        return jsonify({'error': err or 'Failed to update student'}), 400

    return jsonify({
        'status': 'success',
        'message': f"Student {stu_id} updated in MongoDB Atlas",
        'data': updated_doc
    }), 200


@mongo_api_bp.route('/students/<student_id>', methods=['DELETE'])
@login_required
@roles_required('Admin')
def delete_student(student_id):
    """
    Deletes a student and all related collection documents from MongoDB Atlas.
    """
    stu_id = str(student_id).strip().upper()
    success, err = MongoStudentService.delete_student(stu_id)
    if not success:
        return jsonify({'error': err or f"Student '{stu_id}' not found in MongoDB Atlas"}), 404

    return jsonify({
        'status': 'success',
        'message': f"Student '{stu_id}' and all associated documents deleted from MongoDB Atlas."
    }), 200
