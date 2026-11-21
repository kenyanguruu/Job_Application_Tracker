import os
import time

import pytest

# Configure a test-only secret before importing the OTP service.
os.environ["SECRET_KEY"] = "pytest-only-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from models import db, OTPVerification
from otp_service import (
    create_otp,
    generate_otp,
    hash_otp,
    verify_otp,
)


@pytest.fixture
def database():
    from app import app

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )

    # Use an isolated in-memory database for these tests.
    with app.app_context():
        db.drop_all()
        db.create_all()

        yield

        db.session.remove()
        db.drop_all()


def test_generate_otp_returns_six_digits():
    otp = generate_otp()

    assert len(otp) == 6
    assert otp.isdigit()


def test_hash_otp_is_consistent():
    assert hash_otp("123456") == hash_otp("123456")


def test_create_otp_and_verify_successfully(database):
    otp = create_otp("TEST@example.com", "login")

    assert otp is not None
    assert verify_otp("test@example.com", "login", otp) is True

    # A successfully used code cannot be reused.
    assert verify_otp("test@example.com", "login", otp) is False


def test_wrong_otp_is_rejected(database):
    otp = create_otp("test@example.com", "login")

    assert verify_otp("test@example.com", "login", "000000") is False

    record = OTPVerification.query.filter_by(
        email="test@example.com",
        purpose="login",
    ).first()

    assert record.attempts == 1


def test_otp_resend_cooldown(database):
    first_otp = create_otp("test@example.com", "login")

    second_otp = create_otp("test@example.com", "login")

    assert first_otp is not None
    assert second_otp is None


def test_otp_expires(database):
    otp = create_otp("test@example.com", "login")

    record = OTPVerification.query.filter_by(
        email="test@example.com",
        purpose="login",
    ).first()

    record.expires_at = time.time() - 1
    db.session.commit()

    assert verify_otp("test@example.com", "login", otp) is False


def test_five_wrong_attempts_block_verification(database):
    otp = create_otp("test@example.com", "login")

    for _ in range(5):
        assert (
            verify_otp(
                "test@example.com",
                "login",
                "000000",
            )
            is False
        )

    assert (
        verify_otp(
            "test@example.com",
            "login",
            otp,
        )
        is False
    )
