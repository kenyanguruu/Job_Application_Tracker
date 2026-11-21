import hashlib
import hmac
import os
import secrets
import time

from dotenv import load_dotenv
from models import db, OTPVerification

load_dotenv()

OTP_EXPIRY_SECONDS = 300
OTP_RESEND_COOLDOWN = 60
MAX_OTP_ATTEMPTS = 5


def _otp_secret():
    """
    Use the Flask SECRET_KEY as a server-side pepper.
    Changing SECRET_KEY invalidates any outstanding OTPs.
    """
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY is required to hash verification codes.")
    return secret.encode("utf-8")


def generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp):
    return hmac.new(
        _otp_secret(),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_otp(email, purpose):
    email = email.strip().lower()
    current_time = time.time()

    record = OTPVerification.query.filter_by(
        email=email,
        purpose=purpose,
    ).first()

    if record:
        if current_time - record.last_sent_at < OTP_RESEND_COOLDOWN:
            return None

        db.session.delete(record)
        db.session.flush()

    otp = generate_otp()

    record = OTPVerification(
        email=email,
        purpose=purpose,
        otp_hash=hash_otp(otp),
        expires_at=current_time + OTP_EXPIRY_SECONDS,
        last_sent_at=current_time,
        attempts=0,
        used=False,
    )

    db.session.add(record)
    db.session.commit()

    return otp


def verify_otp(email, purpose, submitted_otp):
    email = email.strip().lower()

    record = OTPVerification.query.filter_by(
        email=email,
        purpose=purpose,
    ).first()

    if not record or record.used:
        return False

    current_time = time.time()

    if current_time > record.expires_at:
        db.session.delete(record)
        db.session.commit()
        return False

    if record.attempts >= MAX_OTP_ATTEMPTS:
        return False

    record.attempts += 1

    try:
        submitted_hash = hash_otp(submitted_otp)
    except RuntimeError:
        db.session.rollback()
        raise

    if not hmac.compare_digest(record.otp_hash, submitted_hash):
        db.session.commit()
        return False

    record.used = True
    db.session.commit()
    return True
