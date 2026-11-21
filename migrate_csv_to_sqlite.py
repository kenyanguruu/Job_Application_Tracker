import os
import csv

from dotenv import load_dotenv
from app import app
from models import db, User, JobApplication, ArchivedApplication

load_dotenv()

OWNER_EMAIL = os.getenv("INITIAL_OWNER_EMAIL")

if not OWNER_EMAIL:
    raise ValueError("INITIAL_OWNER_EMAIL is missing from .env")


def import_applications(csv_file, model, user_id):
    imported = 0
    skipped = 0

    if not os.path.exists(csv_file):
        return imported, skipped

    with open(csv_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            application_id = int(row["application_id"])

            existing = model.query.filter_by(
                user_id=user_id,
                application_id=application_id
            ).first()

            if existing:
                skipped += 1
                continue

            application = model(
                user_id=user_id,
                application_id=application_id,
                company_name=row["company_name"],
                job_title=row["job_title"],
                job_location=row.get("job_location", ""),
                application_date=row.get("application_date", ""),
                interview_date=row.get("interview_date", ""),
                application_status=row["application_status"],
                applicant_name=row.get("applicant_name", ""),
                contact_email=row.get("contact_email", ""),
                phone_number=row.get("phone_number", ""),
                notes=row.get("notes", "")
            )

            db.session.add(application)
            imported += 1

    return imported, skipped


with app.app_context():

    owner = User.query.filter_by(
        email=OWNER_EMAIL.strip().lower()
    ).first()

    if not owner:
        raise ValueError(
            "Owner account not found. Create and verify the account first."
        )

    active_imported, active_skipped = import_applications(
        "data/applications.csv",
        JobApplication,
        owner.id
    )

    archived_imported, archived_skipped = import_applications(
        "data/deleted_applications.csv",
        ArchivedApplication,
        owner.id
    )

    db.session.commit()

    print("CSV migration completed.")
    print("Active applications imported:", active_imported)
    print("Active applications skipped:", active_skipped)
    print("Archived applications imported:", archived_imported)
    print("Archived applications skipped:", archived_skipped)