from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False

        return check_password_hash(self.password_hash, password)

    google_id = db.Column(db.String(255), unique=True, nullable=True)

    email_verified = db.Column(db.Boolean, default=False, nullable=False)

    applications = db.relationship(
        "JobApplication", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    archived_applications = db.relationship(
        "ArchivedApplication", backref="user", lazy=True, cascade="all, delete-orphan"
    )


class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    application_id = db.Column(db.Integer, nullable=False)

    company_name = db.Column(db.String(150), nullable=False)

    job_title = db.Column(db.String(150), nullable=False)

    job_location = db.Column(db.String(150))

    application_date = db.Column(db.String(20))

    interview_date = db.Column(db.String(20))

    application_status = db.Column(db.String(50), nullable=False)

    applicant_name = db.Column(db.String(150))

    contact_email = db.Column(db.String(150))

    phone_number = db.Column(db.String(50))

    notes = db.Column(db.Text)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "application_id", name="unique_user_application_id"
        ),
    )

    def to_dict(self):
        return {
            "application_id": str(self.application_id),
            "company_name": self.company_name,
            "job_title": self.job_title,
            "job_location": self.job_location or "",
            "application_date": self.application_date or "",
            "interview_date": self.interview_date or "",
            "application_status": self.application_status,
            "applicant_name": self.applicant_name or "",
            "contact_email": self.contact_email or "",
            "phone_number": self.phone_number or "",
            "notes": self.notes or "",
        }


class ArchivedApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    application_id = db.Column(db.Integer, nullable=False)

    company_name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_location = db.Column(db.String(150))
    application_date = db.Column(db.String(20))
    interview_date = db.Column(db.String(20))
    application_status = db.Column(db.String(50), nullable=False)
    applicant_name = db.Column(db.String(150))
    contact_email = db.Column(db.String(150))
    phone_number = db.Column(db.String(50))
    notes = db.Column(db.Text)

    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "user_id", "application_id", name="unique_user_archived_application_id"
        ),
    )

    def to_dict(self):
        return {
            "application_id": str(self.application_id),
            "company_name": self.company_name,
            "job_title": self.job_title,
            "job_location": self.job_location or "",
            "application_date": self.application_date or "",
            "interview_date": self.interview_date or "",
            "application_status": self.application_status,
            "applicant_name": self.applicant_name or "",
            "contact_email": self.contact_email or "",
            "phone_number": self.phone_number or "",
            "notes": self.notes or "",
        }


class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(150), nullable=False, index=True)
    purpose = db.Column(db.String(30), nullable=False)

    otp_hash = db.Column(db.String(64), nullable=False)

    expires_at = db.Column(db.Float, nullable=False)
    last_sent_at = db.Column(db.Float, nullable=False)

    attempts = db.Column(db.Integer, default=0, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("email", "purpose", name="unique_email_otp_purpose"),
    )
