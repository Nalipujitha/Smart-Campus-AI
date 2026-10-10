import sys
import argparse
from getpass import getpass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.audit import AuditEvent
from backend.utils.security import validate_password_strength, validate_username, validate_email

def create_admin_account(username, email, password, full_name="System Administrator"):
    """
    Safely creates an initial or new administrative account with password hashing.
    """
    valid_u, u_err = validate_username(username)
    if not valid_u:
        print(f"Error: {u_err}")
        return False

    valid_e, e_err = validate_email(email)
    if not valid_e:
        print(f"Error: {e_err}")
        return False

    valid_p, p_err = validate_password_strength(password)
    if not valid_p:
        print(f"Error: Password does not meet security requirements: {p_err}")
        return False

    app = create_app()
    with app.app_context():
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            print(f"User with username '{username}' or email '{email}' already exists.")
            return False

        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            role='Admin',
            is_active=True,
            must_change_password=False
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.add(AuditEvent(
            user_id=1,
            action="CREATE_INITIAL_ADMIN",
            module="System",
            details=f"Administrative account '{username}' created via secure CLI.",
            ip_address="127.0.0.1"
        ))
        db.session.commit()
        print(f"Success: Administrator account '{username}' ({email}) created successfully!")
        return True

def init_demo_account():
    """
    Safely and idempotently initializes the dedicated demo evaluator account.
    """
    from backend.services.demo_service import get_or_create_demo_user
    app = create_app()
    with app.app_context():
        user = get_or_create_demo_user()
        print(f"Success: Demo Evaluator account '{user.username}' ({user.email}) is active and secured!")
        print(f"Role: {user.role} (Restricted/Read-Only Demo Mode)")
        return True

def main():
    parser = argparse.ArgumentParser(description="Smart Campus Analytics Secure Administration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create-admin subcommand
    admin_parser = subparsers.add_parser("create-admin", help="Create a secure administrator account")
    admin_parser.add_argument("--username", "-u", help="Admin username")
    admin_parser.add_argument("--email", "-e", help="Admin email address")
    admin_parser.add_argument("--password", "-p", help="Admin password (leave blank for secure prompt)")
    admin_parser.add_argument("--fullname", "-f", default="System Administrator", help="Admin full name")

    # init-demo-account subcommand
    subparsers.add_parser("init-demo-account", help="Initialize or activate the dedicated demo evaluator account")

    args = parser.parse_args()

    if args.command == "create-admin":
        username = args.username or input("Enter Admin Username: ").strip()
        email = args.email or input("Enter Admin Email: ").strip()
        password = args.password or getpass("Enter Admin Password: ")
        confirm_pass = getpass("Confirm Admin Password: ") if not args.password else password

        if password != confirm_pass:
            print("Error: Passwords do not match.")
            sys.exit(1)

        success = create_admin_account(username, email, password, args.fullname)
        sys.exit(0 if success else 1)
    elif args.command == "init-demo-account":
        success = init_demo_account()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

