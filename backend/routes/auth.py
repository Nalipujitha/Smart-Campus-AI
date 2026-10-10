from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from backend.extensions import db
from backend.models.user import User
from backend.models.audit import AuditEvent

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    """Retrieves current logged-in user object from session or None."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def get_portal_url_for_role(role):
    """Determines dashboard landing route based on verified server-side role."""
    if role == 'Admin':
        return url_for('admin.dashboard')
    elif role == 'Faculty':
        return url_for('faculty.dashboard')
    elif role in ['Placement_Officer', 'Placement']:
        return url_for('placement.dashboard')
    else:
        return url_for('dashboard.student_dashboard')

def get_login_url_for_path(path):
    """Returns dedicated login URL according to the target path."""
    if path.startswith('/admin'):
        return url_for('auth.admin_login')
    elif path.startswith('/faculty'):
        return url_for('auth.faculty_login')
    elif path.startswith('/placement'):
        return url_for('auth.placement_login')
    else:
        return url_for('auth.student_login')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            flash('Please sign in to access this portal.', 'warning')
            return redirect(get_login_url_for_path(request.path))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles, allow_admin=True):
    """Enforces server-side role check."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required.'}), 401
                return redirect(get_login_url_for_path(request.path))
            
            user_role = session.get('role')
            # Normalize placement role name
            norm_role = 'Placement_Officer' if user_role in ['Placement_Officer', 'Placement'] else user_role
            normalized_allowed = ['Placement_Officer' if r in ['Placement_Officer', 'Placement'] else r for r in allowed_roles]

            is_permitted = (norm_role in normalized_allowed) or (allow_admin and norm_role == 'Admin')

            if not is_permitted:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Access denied: insufficient permissions.'}), 403
                return redirect(url_for('auth.access_denied'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def handle_portal_authentication(allowed_roles, template_path, portal_name, redirect_endpoint, demo_user=None, demo_pass=None):
    """
    Unified, role-enforced authentication handler for dedicated login portals.
    Ensures that only users matching allowed_roles can authenticate through this page.
    """
    # If user is already authenticated
    if 'user_id' in session:
        curr_role = session.get('role')
        norm_curr_role = 'Placement_Officer' if curr_role in ['Placement_Officer', 'Placement'] else curr_role
        norm_allowed = ['Placement_Officer' if r in ['Placement_Officer', 'Placement'] else r for r in allowed_roles]
        
        if norm_curr_role in norm_allowed:
            return redirect(url_for(redirect_endpoint))
        else:
            flash(f"You are currently signed in as {session.get('full_name')} ({curr_role}). Please log out to access the {portal_name}.", "warning")
            return redirect(get_portal_url_for_role(curr_role))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            identifier = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            identifier = request.form.get('username', '').strip()
            password = request.form.get('password', '')

        if not identifier or not password:
            err = "Identifier and password are required."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass)

        # Lookup user by username, email, or student_id
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.student_id == identifier)
        ).first()

        if user and user.check_password(password) and user.is_active:
            # Enforce that user's database role is authorized for this specific portal
            user_norm_role = 'Placement_Officer' if user.role in ['Placement_Officer', 'Placement'] else user.role
            norm_allowed = ['Placement_Officer' if r in ['Placement_Officer', 'Placement'] else r for r in allowed_roles]

            if user_norm_role not in norm_allowed:
                err = f"Access Denied: Your account ({user.role}) does not have permission to log in through the {portal_name}."
                if request.is_json:
                    return jsonify({'error': err}), 403
                flash(err, 'danger')
                return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass), 403

            # Establish authenticated session
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            session['department'] = user.department
            session['student_id'] = user.student_id

            # Write Audit Event
            audit = AuditEvent(
                user_id=user.id,
                action="LOGIN",
                module="Auth",
                details=f"User {user.username} successfully signed in via {portal_name}.",
                ip_address=request.remote_addr
            )
            db.session.add(audit)
            db.session.commit()

            redirect_target = url_for(redirect_endpoint)
            next_url = request.args.get('next')

            if request.is_json:
                return jsonify({
                    'message': f'Logged in to {portal_name} successfully',
                    'user': user.to_dict(),
                    'redirect_url': redirect_target
                })

            flash(f"Welcome back, {user.full_name}!", 'success')
            return redirect(next_url or redirect_target)
        else:
            err = "Invalid username or password, or account is disabled."
            if request.is_json:
                return jsonify({'error': err}), 401
            flash(err, 'danger')
            return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass), 401

    return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass)


# =========================================================================
# 1. Dedicated Student Login Route
# =========================================================================
@auth_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    return handle_portal_authentication(
        allowed_roles=['Student'],
        template_path='auth/student_login.html',
        portal_name='Student Portal',
        redirect_endpoint='dashboard.student_dashboard',
        demo_user='stu_rahul',
        demo_pass='Student@123'
    )


# =========================================================================
# 2. Dedicated Admin Login Route
# =========================================================================
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return handle_portal_authentication(
        allowed_roles=['Admin'],
        template_path='auth/admin_login.html',
        portal_name='Administrator Portal',
        redirect_endpoint='admin.dashboard',
        demo_user='admin',
        demo_pass='Admin@123'
    )


# =========================================================================
# 3. Dedicated Faculty Login Route
# =========================================================================
@auth_bp.route('/faculty/login', methods=['GET', 'POST'])
def faculty_login():
    return handle_portal_authentication(
        allowed_roles=['Faculty'],
        template_path='auth/faculty_login.html',
        portal_name='Faculty Portal',
        redirect_endpoint='faculty.dashboard',
        demo_user='dr.sharma',
        demo_pass='Faculty@123'
    )


# =========================================================================
# 4. Dedicated Placement Officer Login Route
# =========================================================================
@auth_bp.route('/placement/login', methods=['GET', 'POST'])
def placement_login():
    return handle_portal_authentication(
        allowed_roles=['Placement_Officer', 'Placement'],
        template_path='auth/placement_login.html',
        portal_name='Placement Officer Portal',
        redirect_endpoint='placement.dashboard',
        demo_user='placement_officer',
        demo_pass='Placement@123'
    )


# =========================================================================
# 5. Universal Gateway Landing Route
# =========================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the Institutional Portals Gateway with direct links to all four portals.
    Also handles universal POST requests for backward-compatible API clients.
    """
    if 'user_id' in session:
        user_role = session.get('role')
        return redirect(get_portal_url_for_role(user_role))

    if request.method == 'POST':
        # Backward-compatible login handler for automated scripts
        if request.is_json:
            data = request.get_json() or {}
            identifier = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            identifier = request.form.get('username', '').strip()
            password = request.form.get('password', '')

        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.student_id == identifier)
        ).first()

        if user and user.check_password(password) and user.is_active:
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            session['department'] = user.department
            session['student_id'] = user.student_id

            redirect_target = get_portal_url_for_role(user.role)
            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'redirect_url': redirect_target
                })
            return redirect(redirect_target)
        else:
            err = "Invalid username or password, or account is disabled."
            if request.is_json:
                return jsonify({'error': err}), 401
            flash(err, 'danger')

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    user_id = session.get('user_id')
    user_role = session.get('role')
    if user_id:
        audit = AuditEvent(
            user_id=user_id,
            action="LOGOUT",
            module="Auth",
            details="User logged out.",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
        db.session.commit()

    session.clear()
    flash("You have been securely logged out.", "info")
    
    # Redirect to the relevant portal login or gateway
    if user_role == 'Admin':
        return redirect(url_for('auth.admin_login'))
    elif user_role == 'Faculty':
        return redirect(url_for('auth.faculty_login'))
    elif user_role in ['Placement_Officer', 'Placement']:
        return redirect(url_for('auth.placement_login'))
    else:
        return redirect(url_for('auth.student_login'))


@auth_bp.route('/access-denied')
def access_denied():
    user = get_current_user()
    return render_template('access_denied.html', user=user), 403
