import os

import resend

from dotenv import load_dotenv

load_dotenv()


def send_otp_email(recipient_email, otp):
    """Send an OTP verification email using the Resend API."""

    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        print("Email delivery failed: RESEND_API_KEY is missing.")
        return False

    sender_email = os.getenv("EMAIL_FROM", "JobTracker <onboarding@resend.dev>")

    resend.api_key = api_key

    message = f"""
Hello,

Your JobTracker verification code is:

{otp}

This code expires in 5 minutes.

If you did not request this code, you can ignore this email.

JobTracker Team
"""

    try:
        result = resend.Emails.send(
            {
                "from": sender_email,
                "to": [recipient_email],
                "subject": "Your JobTracker Verification Code",
                "text": message,
            }
        )

        print("OTP email sent successfully.")
        return True

    except Exception as error:
        print("Email delivery failed:", error)
        return False
