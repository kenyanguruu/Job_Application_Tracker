import json
import os
from email.utils import parseaddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()


def send_otp_email(recipient_email, otp):
    """Send an OTP verification email using the Brevo API."""

    api_key = os.getenv("BREVO_API_KEY")

    if not api_key:
        print("Email delivery failed: BREVO_API_KEY is missing.")
        return False

    sender_value = os.getenv(
        "EMAIL_FROM",
        "Job Applicant <samuelmutisya2001@gmail.com>",
    )

    sender_name, sender_email = parseaddr(sender_value)

    if not sender_email:
        print("Email delivery failed: EMAIL_FROM is invalid.")
        return False

    message = f"""
Hello,

Your JobTracker verification code is:

{otp}

This code expires in 5 minutes.

If you did not request this code, you can ignore this email.

JobTracker Team
"""

    payload = {
        "sender": {
            "name": sender_name or "Job Applicant",
            "email": sender_email,
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": "Your JobTracker Verification Code",
        "textContent": message,
    }

    request = Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            print("OTP email accepted by Brevo.")
            return response.status in (200, 201, 202)

    except HTTPError as error:
        error_details = error.read().decode("utf-8", errors="replace")
        print("Brevo email error:", error.code, error_details)
        return False

    except URLError as error:
        print("Brevo connection error:", error.reason)
        return False

    except Exception as error:
        print("Email delivery failed:", error)
        return False
