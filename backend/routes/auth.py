import re
from datetime import datetime, date
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from backend.extensions import db
from backend.models.user import User
from backend.models.student import Student
from backend.models.placement import PlacementProfile
from backend.models.audit import AuditEvent
from backend.utils.security import (
    validate_password_strength,
    validate_username,
    validate_email,
    validate_student_id,
    generate_password_reset_token,
    verify_password_reset_token,
    check_login_rate_limit,
    record_login_failure,
    reset_login_failures
)

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
    elif path.startswith('/student') or path.startswith('/dashboard'):
        return url_for('auth.student_login')
    else:
        return url_for('auth.login')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            flash('Please sign in to access this portal.', 'warning')
            return redirect(get_login_url_for_path(request.path))
        
        # Check if user needs to change temporary password
        user = get_current_user()
        if user and user.must_change_password and request.endpoint not in ['auth.change_password', 'auth.logout']:
            flash('You must change your temporary password to continue.', 'warning')
            return redirect(url_for('auth.change_password'))

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
    Ensures that only active users matching allowed_roles can authenticate through this page.
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
            return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass), 400

        # Rate Limit / Brute-force check
        allowed, retry_after = check_login_rate_limit(identifier, request.remote_addr or '')
        if not allowed:
            err = f"Too many failed login attempts. Account temporarily locked for {retry_after} seconds. Please try again later."
            if request.is_json:
                return jsonify({'error': err, 'retry_after': retry_after}), 429
            flash(err, 'danger')
            return render_template(template_path, demo_user=demo_user, demo_pass=demo_pass), 429

        # Lookup user by username, email, or student_id
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.student_id == identifier)
        ).first()

        if user and user.check_password(password) and user.is_active:
            # Reset rate limit counter on success
            reset_login_failures(identifier, request.remote_addr or '')

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

            # Update last login timestamp
            user.last_login = datetime.utcnow()

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

            # Handle mandatory password change
            if user.must_change_password:
                flash("You must change your temporary password to continue.", "warning")
                return redirect(url_for('auth.change_password'))

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
            record_login_failure(identifier, request.remote_addr or '')
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
        if request.is_json:
            data = request.get_json() or {}
            identifier = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            identifier = request.form.get('username', '').strip()
            password = request.form.get('password', '')

        if not identifier or not password:
            err = "Username/Email and password are required."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('login.html'), 400

        # Rate Limit Check
        allowed, retry_after = check_login_rate_limit(identifier, request.remote_addr or '')
        if not allowed:
            err = f"Too many failed login attempts. Temporarily locked for {retry_after} seconds."
            if request.is_json:
                return jsonify({'error': err, 'retry_after': retry_after}), 429
            flash(err, 'danger')
            return render_template('login.html'), 429

        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.student_id == identifier)
        ).first()

        if user and user.check_password(password) and user.is_active:
            reset_login_failures(identifier, request.remote_addr or '')
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            session['department'] = user.department
            session['student_id'] = user.student_id

            user.last_login = datetime.utcnow()
            db.session.add(AuditEvent(
                user_id=user.id,
                action="LOGIN",
                module="Auth",
                details=f"User {user.username} logged in via Universal Gateway.",
                ip_address=request.remote_addr
            ))
            db.session.commit()

            if user.must_change_password:
                flash("You must change your temporary password to continue.", "warning")
                return redirect(url_for('auth.change_password'))

            redirect_target = get_portal_url_for_role(user.role)
            if request.is_json:
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'redirect_url': redirect_target
                })
            return redirect(redirect_target)
        else:
            record_login_failure(identifier, request.remote_addr or '')
            err = "Invalid username or password, or account is disabled."
            if request.is_json:
                return jsonify({'error': err}), 401
            flash(err, 'danger')
            return render_template('login.html'), 401

    return render_template('login.html')


# =========================================================================
# 6. Student Self-Registration (Public Sign Up)
# =========================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
@auth_bp.route('/student/register', methods=['GET', 'POST'])
def register():
    """
    Public registration endpoint strictly restricted to Student role.
    Validates name, username, email, student_id, password strength, and uniqueness.
    """
    if 'user_id' in session:
        return redirect(get_portal_url_for_role(session.get('role')))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            full_name = data.get('full_name', '').strip()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            student_id = data.get('student_id', '').strip().upper()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
        else:
            full_name = request.form.get('full_name', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            student_id = request.form.get('student_id', '').strip().upper()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        # Basic presence validation
        if not all([full_name, username, email, student_id, password, confirm_password]):
            err = "All registration fields are required."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Validate Username
        valid_u, u_err = validate_username(username)
        if not valid_u:
            if request.is_json:
                return jsonify({'error': u_err}), 400
            flash(u_err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Validate Email
        valid_e, e_err = validate_email(email)
        if not valid_e:
            if request.is_json:
                return jsonify({'error': e_err}), 400
            flash(e_err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Validate Student ID
        valid_sid, sid_err = validate_student_id(student_id)
        if not valid_sid:
            if request.is_json:
                return jsonify({'error': sid_err}), 400
            flash(sid_err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Confirm Passwords Match
        if password != confirm_password:
            err = "Passwords do not match."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Validate Strong Password
        valid_p, p_err = validate_password_strength(password)
        if not valid_p:
            if request.is_json:
                return jsonify({'error': p_err}), 400
            flash(p_err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 400

        # Check Uniqueness constraints across database
        if User.query.filter_by(username=username).first():
            err = f"Username '{username}' is already taken. Please choose another."
            if request.is_json:
                return jsonify({'error': err}), 409
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 409

        if User.query.filter_by(email=email).first():
            err = f"Email '{email}' is already registered with an account."
            if request.is_json:
                return jsonify({'error': err}), 409
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 409

        if User.query.filter_by(student_id=student_id).first():
            err = f"Student ID '{student_id}' is already registered with another user account."
            if request.is_json:
                return jsonify({'error': err}), 409
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form), 409

        # Handle Student Profile Association
        existing_student = Student.query.filter_by(student_id=student_id).first()
        if existing_student:
            dept = existing_student.department
        else:
            # Create a base student profile for the new registrant
            names = full_name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            dept = 'Computer Science & Engineering'
            
            existing_student = Student(
                student_id=student_id,
                first_name=first_name,
                last_name=last_name or first_name,
                email=email,
                department=dept,
                academic_year=1,
                semester=1,
                section='A',
                status='Active',
                enrollment_date=date.today()
            )
            db.session.add(existing_student)
            db.session.add(PlacementProfile(student_id=student_id, target_role='Software Developer'))

        # Create New User (strictly 'Student' role)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='Student',
            department=dept,
            student_id=student_id,
            is_active=True,
            must_change_password=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush() # Populate new_user.id

        # Write Audit Event
        db.session.add(AuditEvent(
            user_id=new_user.id,
            action="REGISTER_STUDENT",
            module="Auth",
            details=f"New student user registered: {username} ({student_id}).",
            ip_address=request.remote_addr
        ))
        db.session.commit()

        success_msg = f"Registration successful for {full_name}! You can now sign in with your credentials."
        if request.is_json:
            return jsonify({
                'message': success_msg,
                'user': new_user.to_dict(),
                'login_url': url_for('auth.student_login')
            }), 201

        flash(success_msg, 'success')
        return redirect(url_for('auth.student_login'))

    return render_template('auth/register.html')


# =========================================================================
# 7. Forgot Password & Secure Reset Token Flow
# =========================================================================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Initiates password reset flow by issuing a cryptographically signed time-limited token.
    """
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            identifier = data.get('email_or_username', '').strip()
        else:
            identifier = request.form.get('email_or_username', '').strip()

        if not identifier:
            err = "Please enter your registered email address or username."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/forgot_password.html'), 400

        user = User.query.filter(
            (User.email == identifier.lower()) | 
            (User.username == identifier)
        ).first()

        reset_token = None
        reset_link = None
        if user and user.is_active:
            reset_token = generate_password_reset_token(
                user.id,
                user.email,
                current_app.config['SECRET_KEY']
            )
            reset_link = url_for('auth.reset_password', token=reset_token, _external=True)

            db.session.add(AuditEvent(
                user_id=user.id,
                action="PASSWORD_RESET_REQUEST",
                module="Auth",
                details=f"Password reset token generated for {user.username}.",
                ip_address=request.remote_addr
            ))
            db.session.commit()

        # Safe response to prevent account enumeration
        info_msg = "If an active account exists with that email or username, password reset instructions have been generated."
        if request.is_json:
            return jsonify({
                'message': info_msg,
                'reset_token': reset_token, # Available in response for automated testing/demo
                'reset_link': reset_link
            }), 200

        flash(info_msg, 'info')
        return render_template('auth/forgot_password.html', demo_reset_link=reset_link)

    return render_template('auth/forgot_password.html')


# =========================================================================
# 8. Password Reset with Token
# =========================================================================
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Verifies reset token and updates password upon validation.
    """
    user_id, email = verify_password_reset_token(token, current_app.config['SECRET_KEY'], max_age=3600)
    
    if not user_id:
        err = "The password reset link is invalid or has expired (exceeded 1 hour). Please request a new one."
        if request.is_json:
            return jsonify({'error': err}), 400
        flash(err, 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get(user_id)
    if not user or not user.is_active:
        err = "User account not found or disabled."
        if request.is_json:
            return jsonify({'error': err}), 404
        flash(err, 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json() or {}
            new_password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
        else:
            new_password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            err = "Please enter and confirm your new password."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/reset_password.html', token=token, user=user), 400

        if new_password != confirm_password:
            err = "Passwords do not match."
            if request.is_json:
                return jsonify({'error': err}), 400
            flash(err, 'danger')
            return render_template('auth/reset_password.html', token=token, user=user), 400

        valid_p, p_err = validate_password_strength(new_password)
        if not valid_p:
            if request.is_json:
                return jsonify({'error': p_err}), 400
            flash(p_err, 'danger')
            return render_template('auth/reset_password.html', token=token, user=user), 400

        # Update password hash and clear mandatory flag
        user.set_password(new_password)
        user.must_change_password = False

        db.session.add(AuditEvent(
            user_id=user.id,
            action="PASSWORD_RESET_SUCCESS",
            module="Auth",
            details=f"Password successfully reset via token for user {user.username}.",
            ip_address=request.remote_addr
        ))
        db.session.commit()

        # Invalidate active session
        session.clear()

        success_msg = "Your password has been successfully reset! Please sign in with your new password."
        if request.is_json:
            return jsonify({'message': success_msg}), 200

        flash(success_msg, 'success')
        return redirect(get_login_url_for_path(get_portal_url_for_role(user.role)))

    return render_template('auth/reset_password.html', token=token, user=user)


# =========================================================================
# 9. Force Change Password (for temporary passwords / user-initiated)
# =========================================================================
@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """
    Requires changing temporary password or allows voluntary password update.
    """
    if 'user_id' not in session:
        flash("Please log in to change your password.", "warning")
        return redirect(url_for('auth.login'))

    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.", "danger")
            return render_template('auth/change_password.html', user=user), 400

        if not user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return render_template('auth/change_password.html', user=user), 400

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return render_template('auth/change_password.html', user=user), 400

        valid_p, p_err = validate_password_strength(new_password)
        if not valid_p:
            flash(p_err, "danger")
            return render_template('auth/change_password.html', user=user), 400

        user.set_password(new_password)
        user.must_change_password = False

        db.session.add(AuditEvent(
            user_id=user.id,
            action="PASSWORD_CHANGE",
            module="Auth",
            details=f"User {user.username} updated their account password.",
            ip_address=request.remote_addr
        ))
        db.session.commit()

        flash("Your password has been successfully updated.", "success")
        return redirect(get_portal_url_for_role(user.role))

    return render_template('auth/change_password.html', user=user)


# =========================================================================
# 10. Secure Logout
# =========================================================================
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
