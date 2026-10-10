from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from backend.routes.auth import login_required, roles_required, get_current_user
from backend.services.campus_assistant import CampusAssistantService
from backend.models.audit import CampusKnowledge
from backend.extensions import db

from backend.models.chat import ChatConversation
from backend.services.gemini_service import GeminiService

campus_bp = Blueprint('campus', __name__)

@campus_bp.route('/')
@login_required
def index():
    user = get_current_user()
    kb_entries = CampusKnowledge.query.filter_by(is_verified=True).all()
    categories = sorted(list(set(e.category for e in kb_entries)))
    
    # Load user's conversations
    conversations = []
    if user:
        conversations = ChatConversation.query.filter_by(
            user_id=user.id,
            is_deleted=False
        ).order_by(ChatConversation.updated_at.desc()).all()

    return render_template(
        'campus_assistant.html',
        user=user,
        kb_entries=kb_entries,
        categories=categories,
        conversations=conversations,
        gemini_configured=GeminiService.is_configured(),
        gemini_model=GeminiService.get_model()
    )

@campus_bp.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.get_json() if request.is_json else request.form
    question = data.get('question', '').strip()

    result = CampusAssistantService.query(question)
    return jsonify(result)

@campus_bp.route('/kb/create', methods=['POST'])
@login_required
@roles_required('Admin', 'Faculty')
def add_kb_entry():
    category = request.form.get('category', '').strip()
    topic = request.form.get('topic', '').strip()
    keywords = request.form.get('keywords', '').strip()
    content = request.form.get('content', '').strip()
    contact_person = request.form.get('contact_person', '').strip()
    contact_email = request.form.get('contact_email', '').strip()

    if not category or not topic or not content:
        flash("Category, Topic, and Content are required.", "danger")
        return redirect(url_for('campus.index'))

    entry = CampusKnowledge(
        category=category,
        topic=topic,
        keywords=keywords,
        content=content,
        contact_person=contact_person,
        contact_email=contact_email,
        is_verified=True
    )
    db.session.add(entry)
    db.session.commit()

    flash(f"Knowledge Base entry '{topic}' created successfully.", "success")
    return redirect(url_for('campus.index'))
