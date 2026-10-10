"""
AI Chat & Conversational Campus Assistant API Blueprint.
Handles multi-turn conversational AI with Google Gemini LLM, verified campus knowledge grounding,
authenticated student context injection, and conversation persistence.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session
from backend.extensions import db
from backend.models.user import User
from backend.models.chat import ChatConversation, ChatMessage
from backend.routes.auth import get_current_user, login_required
from backend.services.gemini_service import GeminiService
from backend.services.campus_assistant import CampusAssistantService

ai_bp = Blueprint('ai_chat', __name__)

# Register both /api/ai and /api/v1/campus-ai routes

def _get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


@ai_bp.route('/api/ai/chat', methods=['POST'])
@ai_bp.route('/api/v1/campus-ai/chat', methods=['POST'])
def chat():
    """
    POST /api/ai/chat & /api/v1/campus-ai/chat
    Main conversational LLM endpoint with RAG context and persistent history.
    """
    if not request.is_json and request.content_type != 'application/json':
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({
                "success": False,
                "error": "Request content must be application/json.",
                "status_code": 400
            }), 400
    else:
        data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid request body. A JSON object with a 'message' field is required.",
            "status_code": 400
        }), 400

    # Accept 'message', or fallback aliases 'prompt', 'question'
    user_message = data.get('message')
    if user_message is None and 'prompt' in data:
        user_message = data.get('prompt')
    elif user_message is None and 'question' in data:
        user_message = data.get('question')

    # Validate message
    is_valid, validation_error = GeminiService.validate_message(user_message)
    if not is_valid:
        return jsonify({
            "success": False,
            "error": validation_error,
            "status_code": 400
        }), 400

    user_message = user_message.strip()
    current_user = get_current_user()
    client_ip = _get_client_ip()

    # 1. Handle Conversation Persistence & Ownership
    conversation = None
    conv_id = data.get('conversation_id')

    if conv_id:
        try:
            conv_id = int(conv_id)
            conversation = ChatConversation.query.filter_by(id=conv_id, is_deleted=False).first()
            if not conversation:
                return jsonify({
                    "success": False,
                    "error": "Conversation not found or has been deleted.",
                    "status_code": 404
                }), 404
            # Verify user ownership if authenticated
            if current_user and conversation.user_id != current_user.id:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized access to this conversation.",
                    "status_code": 403
                }), 403
        except (ValueError, TypeError):
            pass

    # Auto-create conversation if authenticated and none provided
    if not conversation and current_user:
        title = (user_message[:35] + '...') if len(user_message) > 35 else user_message
        conversation = ChatConversation(
            user_id=current_user.id,
            title=title,
            model_name=GeminiService.get_model()
        )
        db.session.add(conversation)
        db.session.commit()

    # 2. Build Verified Context (RAG & Student Profile)
    verified_knowledge = CampusAssistantService.get_verified_knowledge_context(user_message)
    student_context = ""
    if current_user:
        student_context = CampusAssistantService.build_authenticated_student_context(current_user)

    combined_verified_context = ""
    if verified_knowledge:
        combined_verified_context += verified_knowledge + "\n\n"
    if student_context:
        combined_verified_context += student_context

    # 3. Retrieve Conversation History for Multi-Turn Context
    chat_history = data.get('history') or []
    if not chat_history and conversation:
        # Fetch last 8 messages from database
        db_msgs = conversation.messages.order_by(ChatMessage.created_at.desc()).limit(8).all()
        db_msgs.reverse()
        chat_history = [
            {"role": "user" if m.sender == "user" else "model", "text": m.content}
            for m in db_msgs
        ]

    system_instruction = data.get('system_instruction')

    # 4. Generate LLM Response
    response_data, status_code = GeminiService.generate_chat_response(
        message=user_message,
        client_ip=client_ip,
        system_instruction=system_instruction,
        chat_history=chat_history,
        verified_context=combined_verified_context if combined_verified_context else None
    )

    if status_code == 200 and response_data.get('success'):
        ai_reply = response_data.get('reply', '')
        model_name = response_data.get('model', GeminiService.get_model())
        is_fallback = response_data.get('is_fallback', False)
        verified_used = response_data.get('verified_context_used', bool(combined_verified_context))

        # Save to database if conversation exists
        if conversation:
            user_msg = ChatMessage(
                conversation_id=conversation.id,
                sender='user',
                content=user_message,
                model_name=model_name,
                is_fallback=False,
                verified_context_used=False
            )
            ai_msg = ChatMessage(
                conversation_id=conversation.id,
                sender='model',
                content=ai_reply,
                model_name=model_name,
                is_fallback=is_fallback,
                verified_context_used=verified_used
            )
            conversation.updated_at = datetime.utcnow()
            db.session.add(user_msg)
            db.session.add(ai_msg)
            db.session.commit()

            response_data['conversation_id'] = conversation.id
            response_data['message_id'] = ai_msg.id
            response_data['conversation_title'] = conversation.title

    return jsonify(response_data), status_code


# ============================================================================
# CONVERSATION MANAGEMENT REST APIS
# ============================================================================

@ai_bp.route('/api/v1/campus-ai/conversations', methods=['GET'])
@login_required
def list_conversations():
    """List all active conversations for the authenticated user."""
    user = get_current_user()
    conversations = ChatConversation.query.filter_by(
        user_id=user.id,
        is_deleted=False
    ).order_by(ChatConversation.updated_at.desc()).all()

    return jsonify({
        "success": True,
        "conversations": [c.to_dict() for c in conversations]
    }), 200


@ai_bp.route('/api/v1/campus-ai/conversations', methods=['POST'])
@login_required
def create_conversation():
    """Create a new empty conversation for the authenticated user."""
    user = get_current_user()
    data = request.get_json() or {}
    title = data.get('title', 'New Chat').strip() or 'New Chat'

    conversation = ChatConversation(
        user_id=user.id,
        title=title[:100],
        model_name=GeminiService.get_model()
    )
    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        "success": True,
        "conversation": conversation.to_dict()
    }), 201


@ai_bp.route('/api/v1/campus-ai/conversations/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation(conversation_id):
    """Retrieve details and messages of a specific conversation."""
    user = get_current_user()
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        user_id=user.id,
        is_deleted=False
    ).first()

    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found."}), 404

    return jsonify({
        "success": True,
        "conversation": conversation.to_dict(include_messages=True, message_limit=100)
    }), 200


@ai_bp.route('/api/v1/campus-ai/conversations/<int:conversation_id>', methods=['PATCH'])
@login_required
def rename_conversation(conversation_id):
    """Rename a conversation."""
    user = get_current_user()
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        user_id=user.id,
        is_deleted=False
    ).first()

    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found."}), 404

    data = request.get_json() or {}
    new_title = data.get('title', '').strip()
    if not new_title:
        return jsonify({"success": False, "error": "Title cannot be empty."}), 400

    conversation.title = new_title[:100]
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "conversation": conversation.to_dict()
    }), 200


@ai_bp.route('/api/v1/campus-ai/conversations/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Soft-delete a conversation."""
    user = get_current_user()
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        user_id=user.id,
        is_deleted=False
    ).first()

    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found."}), 404

    conversation.is_deleted = True
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Conversation deleted successfully."
    }), 200


@ai_bp.route('/api/v1/campus-ai/conversations/<int:conversation_id>/clear', methods=['POST'])
@login_required
def clear_conversation_messages(conversation_id):
    """Clear all messages within a conversation while keeping the thread."""
    user = get_current_user()
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        user_id=user.id,
        is_deleted=False
    ).first()

    if not conversation:
        return jsonify({"success": False, "error": "Conversation not found."}), 404

    ChatMessage.query.filter_by(conversation_id=conversation.id).delete()
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Conversation history cleared successfully."
    }), 200
