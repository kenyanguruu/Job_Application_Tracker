import os
import re
import time
from datetime import date, timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)
from flask_login import (
    LoginManager,
    login_required,
    current_user,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from dashboard import calculate_dashboard
from email_service import send_otp_email
from otp_service import create_otp, verify_otp

from models import (
    db,
    User,
    JobApplication,
    ArchivedApplication,
    OTPVerification,
)

# --------------------------------------------------
# 1. ENVIRONMENT AND FLASK CONFIGURATION
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

# Recognize HTTPS requests forwarded by Render.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1,
)

# Secret key
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing from environment variables")

# Database configuration:
# PostgreSQL on Render, SQLite locally.
database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("SQLALCHEMY_DATABASE_URI")
    or "sqlite:///jobtracker.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1,
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Session security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv(
        "COOKIE_SECURE",
        "true" if os.getenv("RENDER") else "false",
    )
    .strip()
    .lower()
    == "true"
)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

app.config["WTF_CSRF_TIME_LIMIT"] = 3600

db.init_app(app)
with app.app_context():
    db.create_all()
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access that page."


# --------------------------------------------------
# 2. GOOGLE OAUTH CONFIGURATION
# --------------------------------------------------

oauth = OAuth(app)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )


# --------------------------------------------------
# 3. FLASK-LOGIN USER LOADER
# --------------------------------------------------


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


# --------------------------------------------------
# 4. GENERAL HELPERS
# --------------------------------------------------

VALID_STATUSES = (
    "Applied",
    "Under Review",
    "Interview",
    "Offered",
    "Rejected",
)


def valid_email(email):
    """Check whether an email address has a valid basic format."""
    if not isinstance(email, str):
        return False

    email = email.strip()

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.fullmatch(pattern, email))


def get_user_applications():
    return JobApplication.query.filter_by(user_id=current_user.id).all()


def get_next_user_application_id():
    active_ids = (
        db.session.query(JobApplication.application_id)
        .filter_by(user_id=current_user.id)
        .all()
    )
    archived_ids = (
        db.session.query(ArchivedApplication.application_id)
        .filter_by(user_id=current_user.id)
        .all()
    )
    all_ids = [row[0] for row in active_ids + archived_ids]
    return max(all_ids, default=0) + 1


def get_owned_application(application_id):
    return JobApplication.query.filter_by(
        user_id=current_user.id,
        application_id=application_id,
    ).first()


def get_application_data():
    return [application.to_dict() for application in get_user_applications()]


def clear_pending_authentication():
    session.pop("pending_email", None)
    session.pop("otp_purpose", None)


def send_verification_code(email, purpose):
    """Create an OTP, send it, and remove its record if delivery fails."""
    email = email.strip().lower()
    otp = create_otp(email, purpose)

    if otp is None:
        return False, "Please wait before requesting another code."

    try:
        email_sent = send_otp_email(email, otp)
    except Exception:
        app.logger.exception("Verification email delivery failed.")
        email_sent = False

    if not email_sent:
        record = OTPVerification.query.filter_by(
            email=email,
            purpose=purpose,
        ).first()
        if record:
            db.session.delete(record)
            db.session.commit()
        return False, "We could not send your email. Please try again."

    return True, "Verification code sent successfully."


def begin_otp_flow(email, purpose):
    """Start a fresh, session-bound OTP flow."""
    email = email.strip().lower()
    session.clear()
    session["pending_email"] = email
    session["otp_purpose"] = purpose

    sent, message = send_verification_code(email, purpose)
    if not sent:
        clear_pending_authentication()
        return False, message

    return True, message


def finish_login(user, success_message):
    # Clear pre-authentication session values.
    session.clear()

    # Create the authenticated session.
    login_user(user, fresh=True)

    # Enable the 30-minute sliding session expiry.
    session.permanent = True

    flash(success_message, "success")
    return redirect(url_for("dashboard"))


# --------------------------------------------------
# 5. REGISTRATION
# --------------------------------------------------


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if len(name) > 100:
            flash("Your name is too long.", "error")
            return redirect(url_for("register"))

        if len(email) > 150 or not valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if len(password) < 12:
            flash("Your password must contain at least 12 characters.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Your passwords do not match.", "error")
            return redirect(url_for("register"))

        user = User.query.filter_by(email=email).first()
        created_user = False

        if user and user.email_verified:
            flash("An account already exists with this email. Please log in.", "error")
            return redirect(url_for("login"))

        if user:
            if not user.check_password(password):
                flash(
                    "An unverified account already uses this email. "
                    "Use the password originally entered to continue verification.",
                    "error",
                )
                return redirect(url_for("login"))

        else:
            user = User(
                name=name,
                email=email,
                email_verified=False,
            )
            user.set_password(password)
            db.session.add(user)

            try:
                db.session.commit()
                created_user = True
            except IntegrityError:
                db.session.rollback()
                flash("An account already exists with this email.", "error")
                return redirect(url_for("login"))
            except SQLAlchemyError:
                db.session.rollback()
                app.logger.exception("Registration database operation failed.")
                flash("We could not create your account. Please try again.", "error")
                return redirect(url_for("register"))

        sent, message = begin_otp_flow(email, "registration")

        if not sent:
            if created_user:
                try:
                    OTPVerification.query.filter_by(
                        email=email,
                        purpose="registration",
                    ).delete()
                    db.session.delete(user)
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    app.logger.exception("Could not clean up failed registration.")

            flash(message, "error")
            return redirect(url_for("register"))

        flash("Check your email for your verification code.", "success")
        return redirect(url_for("verify_otp_page"))

    return render_template("register.html")


# --------------------------------------------------
# 6. EMAIL AND PASSWORD LOGIN
# --------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter your email and password.", "error")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        # Allow an owner of a pending registration to request verification again.
        purpose = "login" if user.email_verified else "registration"

        sent, message = begin_otp_flow(email, purpose)
        if not sent:
            flash(message, "error")
            return redirect(url_for("login"))

        if purpose == "registration":
            flash(
                "Your account is not verified. Check your email for a verification code.",
                "success",
            )
        else:
            flash("A login verification code has been sent to your email.", "success")

        return redirect(url_for("verify_otp_page"))

    return render_template("login.html")


# --------------------------------------------------
# 7. GOOGLE LOGIN
# --------------------------------------------------


@app.route("/auth/google")
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash("Google sign-in is not configured yet.", "error")
        return redirect(url_for("login"))

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        redirect_uri = url_for("google_callback", _external=True)

    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            user_info = oauth.google.userinfo()

        if not user_info:
            flash("Google did not return account information.", "error")
            return redirect(url_for("login"))

        raw_email = user_info.get("email")
        raw_name = user_info.get("name")
        email = raw_email.strip().lower() if isinstance(raw_email, str) else ""
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        google_id = user_info.get("sub")
        email_verified = user_info.get("email_verified", False)

        if isinstance(email_verified, str):
            email_verified = email_verified.strip().lower() == "true"

        if (
            not email
            or len(email) > 150
            or not valid_email(email)
            or not isinstance(google_id, str)
            or not google_id
            or not email_verified
        ):
            flash("Google could not verify your email address.", "error")
            return redirect(url_for("login"))

        user = User.query.filter_by(google_id=google_id).first()

        if user:
            # A Google identity must remain attached to the same email account.
            if user.email.lower() != email:
                flash(
                    "The Google account details do not match the linked account.",
                    "error",
                )
                return redirect(url_for("login"))
        else:
            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                # Never auto-link a Google identity to an existing password account.
                flash(
                    "An account already exists with this email. "
                    "Log in using that account first. Automatic account linking is disabled.",
                    "error",
                )
                return redirect(url_for("login"))

            user = User(
                name=(name or email.split("@")[0])[:100],
                email=email,
                google_id=google_id,
                email_verified=True,
            )
            db.session.add(user)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "This Google account could not be registered. Please try again.",
                    "error",
                )
                return redirect(url_for("login"))

        sent, message = begin_otp_flow(email, "login")
        if not sent:
            flash(message, "error")
            return redirect(url_for("login"))

        flash(
            "Google sign-in succeeded. Check your email for the verification code.",
            "success",
        )
        return redirect(url_for("verify_otp_page"))

    except Exception:
        db.session.rollback()
        app.logger.exception("Google authentication failed.")
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("login"))


# --------------------------------------------------
# PASSWORD RESET AND PASSWORDLESS LOGIN
# --------------------------------------------------


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or len(email) > 150 or not valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("forgot_password"))

        user = User.query.filter_by(email=email).first()

        if user and user.email_verified:
            sent, message = begin_otp_flow(email, "password_reset")

            if not sent:
                session["pending_email"] = email
                session["otp_purpose"] = "password_reset"
        else:
            session.clear()
            session["pending_email"] = email
            session["otp_purpose"] = "password_reset"

        flash(
            "If a verified account exists with that email, "
            "a password-reset code will be sent.",
            "success",
        )

        return redirect(url_for("verify_otp_page"))

    return render_template("forgot_password.html")


@app.route("/recover-unverified-account", methods=["GET", "POST"])
def recover_unverified_account():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or len(email) > 150 or not valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("recover_unverified_account"))

        user = User.query.filter_by(email=email).first()

        if user and not user.email_verified:
            begin_otp_flow(email, "registration_recovery")
        else:
            # Keep the response generic for account privacy.
            session.clear()
            session["pending_email"] = email
            session["otp_purpose"] = "registration_recovery"

        flash(
            "If an unverified account exists with that email, "
            "a recovery code will be sent.",
            "success",
        )
        return redirect(url_for("verify_otp_page"))

    return render_template(
        "forgot_password.html",
        recovery_mode=True,
    )


@app.route("/login-with-otp", methods=["GET", "POST"])
def login_with_otp():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or len(email) > 150 or not valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("login_with_otp"))

        user = User.query.filter_by(email=email).first()

        if user and user.email_verified:
            sent, message = begin_otp_flow(email, "login")

            if not sent:
                session["pending_email"] = email
                session["otp_purpose"] = "login"
        else:
            session.clear()
            session["pending_email"] = email
            session["otp_purpose"] = "login"

        flash(
            "If a verified account exists with that email, "
            "a login code will be sent.",
            "success",
        )

        return redirect(url_for("verify_otp_page"))

    return render_template("login_with_otp.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    recovery_mode = "account_recovery_email" in session

    if recovery_mode:
        email = session.get("account_recovery_email")
        verified_at = session.get("account_recovery_verified_at")
    else:
        email = session.get("password_reset_email")
        verified_at = session.get("password_reset_verified_at")

    if not email or not verified_at:
        flash("Please verify your email before resetting your password.", "error")

        if recovery_mode:
            return redirect(url_for("recover_unverified_account"))

        return redirect(url_for("forgot_password"))

    # The authorization expires after five minutes.
    if time.time() - verified_at > 300:
        session.pop("account_recovery_email", None)
        session.pop("account_recovery_verified_at", None)
        session.pop("password_reset_email", None)
        session.pop("password_reset_verified_at", None)

        flash("Your verification session has expired. Request a new code.", "error")

        if recovery_mode:
            return redirect(url_for("recover_unverified_account"))

        return redirect(url_for("forgot_password"))

    user = User.query.filter_by(email=email).first()

    # Recovery is only for existing unverified accounts.
    if (
        not user
        or (recovery_mode and user.email_verified)
        or (not recovery_mode and not user.email_verified)
    ):
        session.pop("account_recovery_email", None)
        session.pop("account_recovery_verified_at", None)
        session.pop("password_reset_email", None)
        session.pop("password_reset_verified_at", None)

        flash("We could not verify this account. Please try again.", "error")

        if recovery_mode:
            return redirect(url_for("recover_unverified_account"))

        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 12:
            flash("Your password must contain at least 12 characters.", "error")
            return redirect(url_for("reset_password"))

        if password != confirm_password:
            flash("Your passwords do not match.", "error")
            return redirect(url_for("reset_password"))

        user.set_password(password)

        # Only verify an unverified account after its recovery is completed.
        if recovery_mode:
            user.email_verified = True

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Password update database operation failed.")
            flash("We could not update your password. Please try again.", "error")
            return redirect(url_for("reset_password"))

        session.pop("account_recovery_email", None)
        session.pop("account_recovery_verified_at", None)
        session.pop("password_reset_email", None)
        session.pop("password_reset_verified_at", None)

        if recovery_mode:
            return finish_login(
                user,
                "Your account has been recovered and verified successfully.",
            )

        return finish_login(user, "Your password has been reset successfully.")

    return render_template("reset_password.html")


# --------------------------------------------------
# 8. OTP VERIFICATION
# --------------------------------------------------


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_page():
    email = session.get("pending_email")
    purpose = session.get("otp_purpose")

    allowed_purposes = (
        "registration",
        "registration_recovery",
        "login",
        "password_reset",
    )

    if not email or purpose not in allowed_purposes:
        flash("Please start the verification process again.", "error")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=email).first()

    if not user and purpose == "registration":
        clear_pending_authentication()
        flash("Account not found. Please register again.", "error")
        return redirect(url_for("register"))

    # Unknown accounts cannot complete authentication or recovery.
    if not user and purpose in (
        "login",
        "password_reset",
        "registration_recovery",
    ):
        if request.method == "POST":
            flash("Invalid or expired verification code.", "error")
            return redirect(url_for("verify_otp_page"))

        return render_template(
            "verify_otp.html",
            email=email,
            purpose=purpose,
        )

    # Login and ordinary password reset require verified accounts.
    if user and purpose in ("login", "password_reset") and not user.email_verified:
        if request.method == "POST":
            flash("Invalid or expired verification code.", "error")
            return redirect(url_for("verify_otp_page"))

        return render_template(
            "verify_otp.html",
            email=email,
            purpose=purpose,
        )

    # Recovery requires an existing unverified account.
    if user and purpose == "registration_recovery" and user.email_verified:
        if request.method == "POST":
            flash("Invalid or expired verification code.", "error")
            return redirect(url_for("verify_otp_page"))

        return render_template(
            "verify_otp.html",
            email=email,
            purpose=purpose,
        )

    if request.method == "POST":
        submitted_otp = request.form.get("otp", "").strip()

        if not re.fullmatch(r"\d{6}", submitted_otp):
            flash("Enter the six-digit verification code.", "error")
            return redirect(url_for("verify_otp_page"))

        if not verify_otp(email, purpose, submitted_otp):
            flash("Invalid or expired verification code.", "error")
            return redirect(url_for("verify_otp_page"))

        # Complete ordinary registration.
        if purpose == "registration":
            user.email_verified = True

            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                app.logger.exception("Could not complete email verification.")
                flash(
                    "Verification could not be completed. Please try again.",
                    "error",
                )
                return redirect(url_for("verify_otp_page"))

            return finish_login(
                user,
                "Your account has been verified successfully.",
            )

        # Authorize recovery of an unverified account.
        if purpose == "registration_recovery":
            session["account_recovery_email"] = email
            session["account_recovery_verified_at"] = time.time()
            clear_pending_authentication()

            flash(
                "Email verified. You can now create a new password.",
                "success",
            )
            return redirect(url_for("reset_password"))

        # Authorize an ordinary password reset.
        if purpose == "password_reset":
            session["password_reset_email"] = email
            session["password_reset_verified_at"] = time.time()
            clear_pending_authentication()

            flash(
                "Email verified. You can now create a new password.",
                "success",
            )
            return redirect(url_for("reset_password"))

        # Complete passwordless login.
        return finish_login(user, "Login successful.")

    return render_template(
        "verify_otp.html",
        email=email,
        purpose=purpose,
    )


# --------------------------------------------------
# 9. RESEND OTP
# --------------------------------------------------


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = session.get("pending_email")
    purpose = session.get("otp_purpose")

    allowed_purposes = (
        "registration",
        "registration_recovery",
        "login",
        "password_reset",
    )

    if not email or purpose not in allowed_purposes:
        flash("Please start the process again.", "error")
        return redirect(url_for("login"))

    user = User.query.filter_by(email=email).first()

    if purpose == "registration":
        if not user:
            clear_pending_authentication()
            flash("Please start registration again.", "error")
            return redirect(url_for("register"))

        if user.email_verified:
            clear_pending_authentication()
            flash("This account is already verified. Please log in.", "success")
            return redirect(url_for("login"))

    # Login and password reset require verified accounts.
    if purpose in ("login", "password_reset"):
        if not user or not user.email_verified:
            flash(
                "If a verified account exists with that email, "
                "a new verification code will be sent.",
                "success",
            )
            return redirect(url_for("verify_otp_page"))

    # Recovery requires an existing unverified account.
    if purpose == "registration_recovery":
        if not user or user.email_verified:
            flash(
                "If an unverified account exists with that email, "
                "a recovery code will be sent.",
                "success",
            )
            return redirect(url_for("verify_otp_page"))

    sent, message = send_verification_code(email, purpose)

    if purpose in ("login", "password_reset"):
        flash(
            "If a verified account exists with that email, "
            "a new verification code will be sent.",
            "success",
        )
    elif purpose == "registration_recovery":
        flash(
            "If an unverified account exists with that email, "
            "a recovery code will be sent.",
            "success",
        )
    elif sent:
        flash("A new verification code has been sent.", "success")
    else:
        flash(message, "error")

    return redirect(url_for("verify_otp_page"))


# --------------------------------------------------
# 10. LOGOUT
# --------------------------------------------------


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# --------------------------------------------------
# 11. APPLICATION HOMEPAGE
# --------------------------------------------------


@app.route("/")
@app.route("/applications")
@login_required
def home():
    applications = get_application_data()
    return render_template("index.html", applications=applications)


# --------------------------------------------------
# 12. FILTER APPLICATIONS BY STATUS
# --------------------------------------------------


@app.route("/applications/status/<status>")
@login_required
def status_applications(status):
    if status not in VALID_STATUSES:
        return "Invalid application status.", 404

    applications = [
        application.to_dict()
        for application in JobApplication.query.filter_by(
            user_id=current_user.id,
            application_status=status,
        ).all()
    ]
    return render_template("index.html", applications=applications)


# --------------------------------------------------
# 13. SEARCH APPLICATIONS
# --------------------------------------------------


@app.route("/search")
@login_required
def search_applications():
    query = request.args.get("query", "").strip().lower()
    applications = get_application_data()

    if query:
        applications = [
            application
            for application in applications
            if query in application["company_name"].lower()
            or query in application["job_title"].lower()
            or query in application["application_status"].lower()
            or query in application["job_location"].lower()
            or query in application["application_id"].lower()
        ]

    return render_template("index.html", applications=applications)


# --------------------------------------------------
# 14. APPLICATION DETAILS
# --------------------------------------------------


@app.route("/application/<int:application_id>")
@login_required
def application_details(application_id):
    application = get_owned_application(application_id)
    if application is None:
        return "Application not found.", 404

    return render_template(
        "application_details.html",
        application=application.to_dict(),
    )


# --------------------------------------------------
# 15. EDIT APPLICATION PAGE
# --------------------------------------------------


@app.route("/application/<int:application_id>/edit")
@login_required
def edit_application(application_id):
    application = get_owned_application(application_id)
    if application is None:
        return "Application not found.", 404

    return render_template(
        "edit_application.html",
        application=application.to_dict(),
    )


# --------------------------------------------------
# 16. UPDATE APPLICATION
# --------------------------------------------------


@app.route("/application/<int:application_id>/update", methods=["POST"])
@login_required
def update_application(application_id):
    application = get_owned_application(application_id)
    if application is None:
        return "Application not found.", 404

    company_name = request.form.get("company_name", "").strip()
    job_title = request.form.get("job_title", "").strip()
    job_location = request.form.get("job_location", "").strip()
    interview_date = request.form.get("interview_date", "").strip()
    application_status = request.form.get("application_status", "").strip()
    applicant_name = request.form.get("applicant_name", "").strip()
    contact_email = request.form.get("contact_email", "").strip().lower()
    phone_number = request.form.get("phone_number", "").strip()
    notes = request.form.get("notes", "").strip()

    if not all(
        (
            company_name,
            job_title,
            job_location,
            application_status,
            applicant_name,
            contact_email,
            phone_number,
        )
    ):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("edit_application", application_id=application_id))

    if application_status not in VALID_STATUSES:
        flash("Invalid application status.", "error")
        return redirect(url_for("edit_application", application_id=application_id))

    if (
        len(company_name) > 150
        or len(job_title) > 150
        or len(job_location) > 150
        or len(applicant_name) > 150
        or len(contact_email) > 150
        or len(phone_number) > 50
    ):
        flash("One or more fields are too long.", "error")
        return redirect(url_for("edit_application", application_id=application_id))

    if not valid_email(contact_email):
        flash("Please enter a valid contact email address.", "error")
        return redirect(url_for("edit_application", application_id=application_id))

    application.company_name = company_name
    application.job_title = job_title
    application.job_location = job_location
    application.interview_date = interview_date
    application.application_status = application_status
    application.applicant_name = applicant_name
    application.contact_email = contact_email
    application.phone_number = phone_number
    application.notes = notes

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Application update failed.")
        flash("The application could not be updated. Please try again.", "error")
        return redirect(url_for("edit_application", application_id=application_id))

    flash("Application updated successfully!", "success")
    return redirect(url_for("application_details", application_id=application_id))


# --------------------------------------------------
# 17. DELETE AND ARCHIVE APPLICATION
# --------------------------------------------------


@app.route("/application/<int:application_id>/delete", methods=["POST"])
@login_required
def delete_application(application_id):
    application = get_owned_application(application_id)
    if application is None:
        return "Application not found.", 404

    archived_application = ArchivedApplication(
        user_id=current_user.id,
        application_id=application.application_id,
        company_name=application.company_name,
        job_title=application.job_title,
        job_location=application.job_location,
        application_date=application.application_date,
        interview_date=application.interview_date,
        application_status=application.application_status,
        applicant_name=application.applicant_name,
        contact_email=application.contact_email,
        phone_number=application.phone_number,
        notes=application.notes,
    )

    db.session.add(archived_application)
    db.session.delete(application)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Application archive operation failed.")
        flash("The application could not be archived. Please try again.", "error")
        return redirect(url_for("application_details", application_id=application_id))

    flash("Application deleted and archived successfully!", "success")
    return redirect(url_for("home"))


# --------------------------------------------------
# 18. ADD APPLICATION
# --------------------------------------------------


@app.route("/add-application", methods=["POST"])
@login_required
def add_application():
    company_name = request.form.get("company_name", "").strip()
    job_title = request.form.get("job_title", "").strip()
    job_location = request.form.get("job_location", "").strip()
    interview_date = request.form.get("interview_date", "").strip()
    application_status = request.form.get("application_status", "").strip()
    applicant_name = request.form.get("applicant_name", "").strip()
    contact_email = request.form.get("contact_email", "").strip().lower()
    phone_number = request.form.get("phone_number", "").strip()
    notes = request.form.get("notes", "").strip()

    if not all(
        (
            company_name,
            job_title,
            job_location,
            application_status,
            applicant_name,
            contact_email,
            phone_number,
        )
    ):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("home"))

    if application_status not in VALID_STATUSES:
        flash("Invalid application status.", "error")
        return redirect(url_for("home"))

    if (
        len(company_name) > 150
        or len(job_title) > 150
        or len(job_location) > 150
        or len(applicant_name) > 150
        or len(contact_email) > 150
        or len(phone_number) > 50
    ):
        flash("One or more fields are too long.", "error")
        return redirect(url_for("home"))

    if not valid_email(contact_email):
        flash("Please enter a valid contact email address.", "error")
        return redirect(url_for("home"))

    application = JobApplication(
        user_id=current_user.id,
        application_id=get_next_user_application_id(),
        company_name=company_name,
        job_title=job_title,
        job_location=job_location,
        application_date=date.today().isoformat(),
        interview_date=interview_date,
        application_status=application_status,
        applicant_name=applicant_name,
        contact_email=contact_email,
        phone_number=phone_number,
        notes=notes,
    )

    db.session.add(application)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("New application could not be saved.")
        flash("The application could not be saved. Please try again.", "error")
        return redirect(url_for("home"))

    flash("Application saved successfully!", "success")
    return redirect(url_for("home"))


# --------------------------------------------------
# 19. DASHBOARD
# --------------------------------------------------


@app.route("/dashboard")
@login_required
def dashboard():
    applications = get_application_data()
    dashboard_data = calculate_dashboard(applications)
    return render_template("dashboard.html", dashboard=dashboard_data)


# --------------------------------------------------
# 20. ABOUT PAGE
# --------------------------------------------------


@app.route("/about")
def about():
    return "This application helps me manage my job applications."


# --------------------------------------------------
# 21. RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").strip().lower() == "true",
    )
