import os
from datetime import datetime
from backend.extensions import db

EXTENSION_LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.java': 'java',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.json': 'json',
    '.sql': 'sql',
    '.md': 'markdown',
    '.txt': 'plaintext',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml'
}

def detect_language(filename: str) -> str:
    """Detect Monaco language identifier from filename extension."""
    if not filename:
        return 'plaintext'
    _, ext = os.path.splitext(filename.lower())
    return EXTENSION_LANGUAGE_MAP.get(ext, 'plaintext')


class StudentFile(db.Model):
    __tablename__ = 'student_files'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(128), nullable=False)
    file_type = db.Column(db.String(32), default='plaintext', nullable=False)
    content = db.Column(db.Text, default='', nullable=False)
    size_bytes = db.Column(db.Integer, default=0, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    versions = db.relationship('StudentFileVersion', backref='file', lazy=True, cascade='all, delete-orphan', order_by='desc(StudentFileVersion.version_number)')

    def update_content(self, new_content: str, summary: str = 'Saved changes', create_version: bool = True):
        """Updates content, recomputes size, and optionally records version history."""
        self.content = new_content
        self.size_bytes = len(new_content.encode('utf-8'))
        self.updated_at = datetime.utcnow()

        if create_version:
            latest_version = StudentFileVersion.query.filter_by(file_id=self.id).order_by(StudentFileVersion.version_number.desc()).first()
            next_version_num = (latest_version.version_number + 1) if latest_version else 1
            
            # Avoid duplicate versions if content is identical to latest version
            if latest_version and latest_version.content == new_content:
                return None

            ver = StudentFileVersion(
                file_id=self.id,
                student_id=self.student_id,
                version_number=next_version_num,
                content=new_content,
                size_bytes=self.size_bytes,
                change_summary=summary,
                created_at=datetime.utcnow()
            )
            db.session.add(ver)
            return ver
        return None

    def to_dict(self, include_content=True):
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'language': detect_language(self.filename),
            'size_bytes': self.size_bytes,
            'version_count': len(self.versions) if self.versions else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        if include_content:
            data['content'] = self.content
        return data


class StudentFileVersion(db.Model):
    __tablename__ = 'student_file_versions'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('student_files.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    size_bytes = db.Column(db.Integer, default=0, nullable=False)
    change_summary = db.Column(db.String(256), default='Saved changes')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'file_id': self.file_id,
            'student_id': self.student_id,
            'version_number': self.version_number,
            'size_bytes': self.size_bytes,
            'change_summary': self.change_summary,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        if include_content:
            data['content'] = self.content
        return data


class StudentWorkspaceSetting(db.Model):
    __tablename__ = 'student_workspace_settings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), db.ForeignKey('students.student_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    last_opened_file_id = db.Column(db.Integer, nullable=True)
    theme = db.Column(db.String(32), default='vs-dark', nullable=False)
    font_size = db.Column(db.Integer, default=14, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'last_opened_file_id': self.last_opened_file_id,
            'theme': self.theme,
            'font_size': self.font_size,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
