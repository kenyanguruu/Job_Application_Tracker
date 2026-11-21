# Job Application Tracker

A secure Flask application for tracking job applications.

## Features

- User registration and OTP email verification
- Email/password login and Google OAuth
- Add, view, edit, search and delete applications
- Archive applications
- Personal dashboard and statistics
- User-specific application records
- CSRF protection
- SQLite locally and PostgreSQL in production

## Technology

- Python and Flask
- Flask-Login and Flask-WTF
- Flask-SQLAlchemy and SQLAlchemy
- Authlib for Google OAuth
- PostgreSQL and SQLite
- HTML, CSS and JavaScript

## Installation

Clone the repository:

    git clone https://github.com/kenyanguruu/Job_Application_Tracker.git
    cd Job_Application_Tracker

Install dependencies:

    python -m pip install -r requirements.txt

## Environment Variables

Create a local `.env` file containing your own configuration:

    SECRET_KEY=your-long-random-secret
    GOOGLE_CLIENT_ID=your-google-client-id
    GOOGLE_CLIENT_SECRET=your-google-client-secret
    GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/auth/google/callback
    MAIL_SERVER=your-smtp-server
    MAIL_PORT=587
    MAIL_USERNAME=your-email
    MAIL_PASSWORD=your-email-app-password
    COOKIE_SECURE=False
    FLASK_DEBUG=True

Never commit `.env` or publish your credentials.

## Run Locally

    python app.py

Open:

    http://127.0.0.1:5000

## Tests

    python -m pytest

## Production Deployment

The application supports PostgreSQL through the `DATABASE_URL` environment variable.

For Render:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Configure `SECRET_KEY`, `DATABASE_URL`, email settings and Google OAuth settings in the service environment.
- Set the Google OAuth redirect URI to your deployed domain:
  `https://YOUR-RENDER-DOMAIN/auth/google/callback`
- Set `COOKIE_SECURE=True` in production.

Note: Existing local SQLite records are not automatically transferred to PostgreSQL.
