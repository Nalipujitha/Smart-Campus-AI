from backend.routes.auth import auth_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.students import students_bp
from backend.routes.attendance import attendance_bp
from backend.routes.analytics import analytics_bp
from backend.routes.interventions import interventions_bp
from backend.routes.career import career_bp
from backend.routes.learning import learning_bp
from backend.routes.placement import placement_bp
from backend.routes.campus import campus_bp
from backend.routes.admin import admin_bp
from backend.routes.faculty import faculty_bp
from backend.routes.data_import import data_import_bp
from backend.routes.api import api_bp
from backend.routes.ai_chat import ai_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'students_bp',
    'attendance_bp',
    'analytics_bp',
    'interventions_bp',
    'career_bp',
    'learning_bp',
    'placement_bp',
    'campus_bp',
    'admin_bp',
    'faculty_bp',
    'data_import_bp',
    'api_bp',
    'ai_bp',
]
