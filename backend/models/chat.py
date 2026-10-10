from datetime import datetime
from backend.extensions import db

class ChatConversation(db.Model):
    __tablename__ = 'chat_conversations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False, default='New Chat')
    model_name = db.Column(db.String(100), nullable=True, default='gemini-1.5-flash')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan', order_by='ChatMessage.created_at.asc()')
    user = db.relationship('User', backref=db.backref('chat_conversations', lazy='dynamic'))

    def to_dict(self, include_messages=False, message_limit=50):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': self.messages.count()
        }
        if include_messages:
            msgs = self.messages.limit(message_limit).all()
            data['messages'] = [m.to_dict() for m in msgs]
        return data


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'model' / 'assistant'
    content = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(100), nullable=True)
    is_fallback = db.Column(db.Boolean, default=False, nullable=False)
    verified_context_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.sender,
            'role': 'user' if self.sender == 'user' else 'model',
            'content': self.content,
            'text': self.content,
            'model_name': self.model_name,
            'is_fallback': self.is_fallback,
            'verified_context_used': self.verified_context_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
