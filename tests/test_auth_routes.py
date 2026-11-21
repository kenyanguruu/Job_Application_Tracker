import os
import time

# Configure the test environment before importing the Flask app.
os.environ["SECRET_KEY"] = "pytest-only-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
import app as app_module

from models import db, User


@pytest.fixture
def client():
    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app_module.app.app_context():
        db.drop_all()
        db.create_all()

        yield app_module.app.test_client()

        db.session.remove()
        db.drop_all()


def create_verified_user(email="test@example.com"):
    user = User(
        name="Test User",
        email=email,
        email_verified=True,
    )
    user.set_password("TestPassword123!")

    db.session.add(user)
    db.session.commit()

    return user


@pytest.mark.parametrize(
    "route,purpose",
    [
        ("/forgot-password", "password_reset"),
        ("/login-with-otp", "login"),
    ],
)
def test_unknown_email_gets_generic_response(client, route, purpose):
    response = client.post(
        route,
        data={"email": "unknown@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session["otp_purpose"] == purpose
        assert session["pending_email"] == "unknown@example.com"


@pytest.mark.parametrize(
    "route,purpose",
    [
        ("/forgot-password", "password_reset"),
        ("/login-with-otp", "login"),
    ],
)
def test_known_email_gets_generic_response_when_email_fails(
    client,
    monkeypatch,
    route,
    purpose,
):
    create_verified_user()

    monkeypatch.setattr(
        app_module,
        "begin_otp_flow",
        lambda email, otp_purpose: (
            False,
            "Email delivery failed.",
        ),
    )

    response = client.post(
        route,
        data={"email": "test@example.com"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session["otp_purpose"] == purpose
        assert session["pending_email"] == "test@example.com"


def test_reset_password_requires_email_verification(client):
    response = client.get("/reset-password")

    assert response.status_code == 302
    assert "/forgot-password" in response.location


def test_successful_passwordless_login(client, monkeypatch):
    create_verified_user()

    monkeypatch.setattr(
        app_module,
        "verify_otp",
        lambda email, purpose, otp: (
            email == "test@example.com" and purpose == "login" and otp == "123456"
        ),
    )

    with client.session_transaction() as session:
        session["pending_email"] = "test@example.com"
        session["otp_purpose"] = "login"

    response = client.post(
        "/verify-otp",
        data={"otp": "123456"},
    )

    assert response.status_code == 302
    assert "/dashboard" in response.location

    with client.session_transaction() as session:
        assert "_user_id" in session
        assert "pending_email" not in session


def test_successful_password_reset(client, monkeypatch):
    user = create_verified_user()

    monkeypatch.setattr(
        app_module,
        "verify_otp",
        lambda email, purpose, otp: True,
    )

    with client.session_transaction() as session:
        session["pending_email"] = "test@example.com"
        session["otp_purpose"] = "password_reset"

    # Verify the email using the OTP.
    response = client.post(
        "/verify-otp",
        data={"otp": "123456"},
    )

    assert response.status_code == 302
    assert "/reset-password" in response.location

    # The password-reset authorization should now exist.
    with client.session_transaction() as session:
        assert session["password_reset_email"] == "test@example.com"
        assert "password_reset_verified_at" in session

    # Submit the new password.
    response = client.post(
        "/reset-password",
        data={
            "password": "NewSecurePassword123!",
            "confirm_password": "NewSecurePassword123!",
        },
    )

    assert response.status_code == 302
    assert "/dashboard" in response.location

    updated_user = db.session.get(User, user.id)

    assert updated_user.check_password("NewSecurePassword123!")

    with client.session_transaction() as session:
        assert "password_reset_email" not in session
        assert "password_reset_verified_at" not in session
        assert "_user_id" in session


def test_expired_password_reset_session_is_rejected(client):
    create_verified_user()

    with client.session_transaction() as session:
        session["password_reset_email"] = "test@example.com"
        session["password_reset_verified_at"] = 1

    response = client.get("/reset-password")

    assert response.status_code == 302
    assert "/forgot-password" in response.location

    with client.session_transaction() as session:
        assert "password_reset_email" not in session
        assert "password_reset_verified_at" not in session


def test_mismatched_new_passwords_are_rejected(client):
    create_verified_user()

    with client.session_transaction() as session:
        session["password_reset_email"] = "test@example.com"
        session["password_reset_verified_at"] = time.time()

    response = client.post(
        "/reset-password",
        data={
            "password": "NewSecurePassword123!",
            "confirm_password": "DifferentPassword123!",
        },
    )

    assert response.status_code == 302
    assert "/reset-password" in response.location

    user = User.query.filter_by(email="test@example.com").first()

    assert user.check_password("TestPassword123!")
