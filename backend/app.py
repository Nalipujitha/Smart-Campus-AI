import os
import sys
from pathlib import Path

# Add project root to sys.path so 'backend' is recognized as a package
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# pyrefly: ignore [missing-import]
from flask import Flask, render_template, jsonify, request
from backend.config import Config
from backend.extensions import db
from backend.routes.auth import auth_bp, get_current_user
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
from backend.routes.coding_lab import coding_lab_bp
from backend.routes.student_workspace import student_workspace_bp
from backend.routes.mongo_api import mongo_api_bp
from backend.db_mongo import mongo_manager

def create_app(config_class=Config):
    frontend_dir = os.path.join(BASE_DIR, 'frontend')
    template_folder = os.path.join(frontend_dir, 'templates')
    static_folder = os.path.join(frontend_dir, 'static')

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure database tables and initial required schema are created on startup (Render / Docker / Local)
    with app.app_context():
        try:
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri.startswith('sqlite:///') and not db_uri.startswith('sqlite:///:memory:'):
                db_path = db_uri.replace('sqlite:///', '')
                if not os.path.isabs(db_path):
                    db_path = os.path.join(BASE_DIR, db_path)
                os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

            # Import all models to register them in SQLAlchemy metadata
            import backend.models  # noqa: F401

            # Create any missing tables safely
            db.create_all()

            # Safe schema column migrations for existing databases (SQLite & Postgres)
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                if 'users' in inspector.get_table_names():
                    user_cols = [c['name'] for c in inspector.get_columns('users')]
                    with db.engine.connect() as conn:
                        if 'must_change_password' not in user_cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
                            conn.commit()
                        if 'last_login' not in user_cols:
                            conn.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
                            conn.commit()
            except Exception as mig_err:
                app.logger.debug(f"Column migration status: {mig_err}")

            # Seed initial demo / admin users if database is newly initialized
            if not app.config.get('TESTING'):
                from backend.models.user import User
                if User.query.first() is None:
                    from database.seed_data import seed_database
                    seed_database(app)
        except Exception as e:
            app.logger.warning(f"Database startup initialization note: {e}")

    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'current_user': get_current_user(),
            'app_name': 'Smart Campus Analytics'
        }

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(interventions_bp, url_prefix='/interventions')
    app.register_blueprint(career_bp, url_prefix='/career')
    app.register_blueprint(learning_bp, url_prefix='/learning')
    app.register_blueprint(placement_bp, url_prefix='/placement')
    app.register_blueprint(campus_bp, url_prefix='/campus')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(data_import_bp, url_prefix='/data-import')
    app.register_blueprint(api_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(coding_lab_bp)
    app.register_blueprint(student_workspace_bp)
    app.register_blueprint(mongo_api_bp)

    # CLI Commands
    @app.cli.command('create-admin')
    def create_admin_command():
        """CLI command to safely create an administrative account."""
        import click
        from backend.cli import create_admin_account
        username = click.prompt("Admin username", type=str)
        email = click.prompt("Admin email", type=str)
        password = click.prompt("Admin password", hide_input=True, confirmation_prompt=True)
        fullname = click.prompt("Full name", default="System Administrator")
        create_admin_account(username, email, password, fullname)

    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found', 'status_code': 404}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error occurred', 'status_code': 500}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden access', 'status_code': 403}), 403
        return render_template('access_denied.html'), 403

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
