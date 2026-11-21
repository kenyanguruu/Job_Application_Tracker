
import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_otp_email(recipient_email, otp):

    message = EmailMessage()

    message["Subject"] = "Your JobTracker Verification Code"
    message["From"] = os.getenv("MAIL_USERNAME")
    message["To"] = recipient_email

    message.set_content(
        f"""
Hello,

Your JobTracker verification code is:

{otp}

This code expires in 5 minutes.

If you did not request this code, you can ignore this email.

JobTracker Team
"""
    )

    try:
        with smtplib.SMTP(
            os.getenv("MAIL_SERVER"),
            int(os.getenv("MAIL_PORT"))
        ) as server:

            server.starttls()

            server.login(
                os.getenv("MAIL_USERNAME"),
                os.getenv("MAIL_PASSWORD")
            )

            server.send_message(message)

        return True

    except Exception as error:
        print("Email delivery failed:", error)
        return False
