import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
dotenv_path = BASE_DIR / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-campus-super-secret-key-2026-prod-ready')
    
    # Handle both DATABASE_URL (standard Render env var) and DATABASE_URI
    _db_uri = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI')
    if _db_uri:
        # Render PostgreSQL URIs start with postgres://, but SQLAlchemy requires postgresql://
        if _db_uri.startswith('postgres://'):
            _db_uri = _db_uri.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = _db_uri
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'smart_campus.db')}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Cookie & Security Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    # Demo Login Configuration for Evaluators / Judges
    DEMO_LOGIN_ENABLED = os.environ.get('DEMO_LOGIN_ENABLED', 'True').lower() in ('true', '1', 'yes')
    DEMO_ADMIN_USERNAME = os.environ.get('DEMO_ADMIN_USERNAME', 'demo_evaluator')
    DEMO_ADMIN_PASSWORD = os.environ.get('DEMO_ADMIN_PASSWORD', '')

    # Upload folder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'database', 'data')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max
    
    # Success Scoring Weights (must sum to 1.0)
    WEIGHTS = {
        'academic': float(os.environ.get('WEIGHT_ACADEMIC', 0.30)),
        'attendance': float(os.environ.get('WEIGHT_ATTENDANCE', 0.20)),
        'lms': float(os.environ.get('WEIGHT_LMS', 0.10)),
        'engagement': float(os.environ.get('WEIGHT_ENGAGEMENT', 0.10)),
        'placement': float(os.environ.get('WEIGHT_PLACEMENT', 0.15)),
        'skills': float(os.environ.get('WEIGHT_SKILLS', 0.10)),
        'feedback': float(os.environ.get('WEIGHT_FEEDBACK', 0.05)),
    }
    
    # Attendance Policy Config
    ATTENDANCE_WARNING_THRESHOLD = float(os.environ.get('ATTENDANCE_WARNING_THRESHOLD', 75.0))
    ATTENDANCE_CRITICAL_THRESHOLD = float(os.environ.get('ATTENDANCE_CRITICAL_THRESHOLD', 65.0))
    ATTENDANCE_EXCLUDE_APPROVED_LEAVE = True  # If true, approved leaves are subtracted from denominator
    
    # Risk Classification Thresholds
    RISK_HIGH_THRESHOLD = float(os.environ.get('RISK_HIGH_THRESHOLD', 50.0))
    RISK_MEDIUM_THRESHOLD = float(os.environ.get('RISK_MEDIUM_THRESHOLD', 75.0))

    # Gemini AI Integration Config
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    GEMINI_RATE_LIMIT_PER_MINUTE = int(os.environ.get('GEMINI_RATE_LIMIT_PER_MINUTE', 20))

    # MongoDB Atlas Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI', '')
    MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'smart_campus_db')
    MONGO_USERNAME = os.environ.get('MONGO_USERNAME', '')
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', '')
    MONGO_CLUSTER_HOST = os.environ.get('MONGO_CLUSTER_HOST', '')

class TestConfig(Config):

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
