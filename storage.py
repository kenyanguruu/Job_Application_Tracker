import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CSV_FILE = os.path.join(DATA_DIR, "applications.csv")
DELETED_CSV_FILE = os.path.join(DATA_DIR, "deleted_applications.csv")
ID_FILE = os.path.join(DATA_DIR, "next_application_id.txt")

os.makedirs(DATA_DIR, exist_ok=True)

FIELDNAMES = [
    "application_id",
    "company_name",
    "job_title",
    "job_location",
    "application_date",
    "interview_date",
    "application_status",
    "applicant_name",
    "contact_email",
    "phone_number",
    "notes",
]


def save_application(application):
    file_exists = os.path.exists(CSV_FILE)
    file_is_empty = not file_exists or os.path.getsize(CSV_FILE) == 0

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        if file_is_empty:
            writer.writeheader()

        writer.writerow(application)


def save_all_applications(applications):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        writer.writeheader()
        writer.writerows(applications)


def load_applications():
    loaded_applications = []

    if not os.path.exists(CSV_FILE):
        return loaded_applications

    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            loaded_applications.append(row)

    return loaded_applications


def save_deleted_application(application):
    file_exists = os.path.exists(DELETED_CSV_FILE)
    file_is_empty = not file_exists or os.path.getsize(DELETED_CSV_FILE) == 0

    with open(DELETED_CSV_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        if file_is_empty:
            writer.writeheader()

        writer.writerow(application)


def load_deleted_applications():
    deleted_applications = []

    if not os.path.exists(DELETED_CSV_FILE):
        return deleted_applications

    with open(DELETED_CSV_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            deleted_applications.append(row)

    return deleted_applications


def get_highest_application_id():
    highest_id = 0

    for file_path in (CSV_FILE, DELETED_CSV_FILE):

        if not os.path.exists(file_path):
            continue

        with open(file_path, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    application_id = int(row["application_id"])
                    highest_id = max(highest_id, application_id)

                except (ValueError, KeyError):
                    continue

    return highest_id


def get_next_application_id():
    highest_id = get_highest_application_id()

    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r", encoding="utf-8") as file:
            try:
                saved_next_id = int(file.read().strip())
            except ValueError:
                saved_next_id = 1
    else:
        saved_next_id = 1

    return max(saved_next_id, highest_id + 1)


def advance_application_id(application_id):
    next_id = application_id + 1

    with open(ID_FILE, "w", encoding="utf-8") as file:
        file.write(str(next_id))


def migrate_applications():
    old_applications = load_applications()

    for index, application in enumerate(old_applications, start=1):
        application["application_id"] = str(index)

    save_all_applications(old_applications)


def migrate_notes_column(file_path):
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        records = list(reader)

    for record in records:
        record["notes"] = record.get("notes", "")

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
