from datetime import date
from storage import (
    save_application,
    load_applications,
    save_all_applications,
    save_deleted_application,
    get_next_application_id,
    advance_application_id,
)

APPLICATION_STATUSES = ("Applied", "Under Review", "Interview", "Offered", "Rejected")


def get_non_empty_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def get_positive_integer(prompt):
    while True:
        try:
            value = int(input(prompt))

            if value > 0:
                return value

            print("Enter a number greater than zero.")

        except ValueError:
            print("Invalid input. Enter a whole number.")


def get_application_status():
    while True:
        status = get_non_empty_text("Enter Application status: ").title()
        if status in APPLICATION_STATUSES:
            return status
        print("Invalid status. Please try again.")


def get_interview_date():
    while True:
        yes_no = input("Do you have an interview scheduled? (yes/no): ").strip().lower()
        if yes_no == "yes":
            while True:
                date_text = input("Enter date in this format YYYY-MM-DD: ").strip()
                try:
                    interview_date = date.fromisoformat(date_text)
                    return interview_date
                except ValueError:
                    print("Invalid date. Please use YYYY-MM-DD.")

        elif yes_no == "no":
            return None

        else:
            print("Enter a yes or no answer.")


def get_valid_email():
    while True:
        email = get_non_empty_text("Enter a valid email: ").lower()
        if "@" in email:
            return email
        else:
            print("Invalid email. Please try again.")


def get_applicant_name():
    while True:
        first_name = get_non_empty_text("Enter your First Name: ").title()
        second_name = input("Enter your Second Name (Optional): ").strip().title()
        last_name = get_non_empty_text("Enter your Last Name: ").title()
        full_name = first_name

        if second_name:
            full_name += f" {second_name}"

        full_name += f" {last_name}"

        return full_name


def get_valid_contact():
    while True:
        contact = input("Enter phone no: ").strip()

        if contact.startswith("07") and len(contact) == 10 and contact.isdigit():
            return contact

        elif (
            contact.startswith("+2547") and len(contact) == 13 and contact[1:].isdigit()
        ):
            return contact

        else:
            print("Invalid phone number.")
            print("Use 0712345678 or +254712345678.")


applications = load_applications()


def generate_application_id():
    existing_application_ids = []

    for application in applications:
        application_id = int(application["application_id"])
        existing_application_ids.append(application_id)

    if not existing_application_ids:
        return 1

    highest_existing_id = max(existing_application_ids)

    return highest_existing_id + 1


def find_application_by_id(application_id):

    for application in applications:
        application_id1 = int(application["application_id"])
        if application_id == application_id1:
            return application

    return None


def update_application():
    print("UPDATE JOB APPLICATION")
    print("===============================")

    application_id = get_positive_integer("Enter Application ID: ")

    application = find_application_by_id(application_id)

    if application is None:
        print("Application not found.")
        return

    print("Application found!")
    print(f"Company: {application['company_name']}")
    print(f"Job Title: {application['job_title']}")

    while True:
        print("===============================")
        print("1. Company Name")
        print("2. Job Title")
        print("3. Job Location")
        print("4. Application Status")
        print("5. Interview Date")
        print("6. Contact Email")
        print("7. Applicant Name")
        print("8. Phone Number")
        print("9. Notes")
        print("10. Return to Main Menu")

        choice = input("Select field to update: ").strip()

        if choice == "1":
            new_company_name = get_non_empty_text("Enter new Company Name: ")
            application["company_name"] = new_company_name
            print("Company name updated successfully!")

        elif choice == "2":
            new_job_title = get_non_empty_text("Enter new Job Title: ")
            application["job_title"] = new_job_title
            print("Job title updated successfully!")

        elif choice == "3":
            new_job_location = get_non_empty_text("Enter new Job Location: ")
            application["job_location"] = new_job_location
            print("Job location updated successfully!")

        elif choice == "4":
            new_status = get_application_status()
            application["application_status"] = new_status
            print("Application status updated successfully!")

        elif choice == "5":
            new_interview_date = get_interview_date()
            application["interview_date"] = new_interview_date
            print("Interview date updated successfully!")

        elif choice == "6":
            new_email = get_valid_email()
            application["contact_email"] = new_email
            print("Contact email updated successfully!")

        elif choice == "7":
            new_applicant_name = get_applicant_name()
            application["applicant_name"] = new_applicant_name
            print("Applicant name updated successfully!")

        elif choice == "8":
            new_phone_number = get_valid_contact()
            application["phone_number"] = new_phone_number
            print("Phone number updated successfully!")

        elif choice == "9":
            new_notes = input("Enter new Notes: ").strip()
            application["notes"] = new_notes
            print("Notes updated successfully!")

        elif choice == "10":
            save_all_applications(applications)
            print("All changes saved successfully!")
            break

        else:
            print("Invalid option. Please try again.")


def delete_application():
    print("DELETE JOB APPLICATION")
    print("===============================")

    application_id = get_positive_integer("Enter Application ID: ")

    application = find_application_by_id(application_id)

    if application is None:
        print("Application not found.")
        return

    print("Application found!")
    print(f"Company: {application['company_name']}")
    print(f"Job Title: {application['job_title']}")
    print(f"Application Status: {application['application_status']}")

    while True:
        yes_no = get_non_empty_text("Enter yes to delete or no to cancel: ").lower()

        if yes_no == "yes":
            save_deleted_application(application)

            applications.remove(application)

            save_all_applications(applications)

            print("Application deleted successfully!")
            print("A copy has been saved to the deleted applications archive.")
            break

        elif yes_no == "no":
            print("Deletion cancelled.")
            break

        else:
            print("Invalid input. Please enter yes or no.")


def add_application():
    print("ADD NEW JOB APPLICATION")
    print("This feature will collect job application details.")

    print("===============================")
    application_id = get_next_application_id()
    company_name = get_non_empty_text("Enter Company name: ")
    job_title = get_non_empty_text("Enter Job Title: ")
    job_location = get_non_empty_text("Enter Job Location: ")
    application_date = date.today()
    interview_date = get_interview_date()

    application_status = get_application_status()
    contact_email = get_valid_email()
    full_name = get_applicant_name()
    contact = get_valid_contact()
    notes = input("Enter Notes (optional): ").strip()

    application = {
        "application_id": application_id,
        "company_name": company_name,
        "job_title": job_title,
        "job_location": job_location,
        "application_status": application_status,
        "applicant_name": full_name,
        "application_date": application_date,
        "interview_date": interview_date,
        "contact_email": contact_email,
        "phone_number": contact,
        "notes": notes,
    }
    save_application(application)
    applications.append(application)
    advance_application_id(application_id)

    print("Application saved successfully!")


def view_applications():
    print("VIEW ALL JOB APPLICATIONS")
    print("===============================")

    if not applications:
        print("No applications found.")
        return

    for application in applications:
        print(f"Application ID: {application['application_id']}")
        print(f"Company: {application['company_name']}")
        print(f"Job title: {application['job_title']}")
        print(f"Job Location: {application['job_location']}")
        print(f"Application Date: {application['application_date']}")
        print(f"Application Status: {application['application_status']}")
        interview_date = application["interview_date"]

        if not interview_date:
            interview_date = "Not scheduled"

        print(f"Interview Date: {interview_date}")
        print(f"Applicant Name: {application['applicant_name']}")
        print(f"Contact Email: {application['contact_email']}")
        print(f"Phone Number: {application['phone_number']}")
        notes = application.get("notes", "")

        if not notes:
            notes = "No notes available"

        print(f"Notes: {notes}")
        print("===============================")


def search_applications():
    print("SEARCH JOB APPLICATIONS")
    print("===============================")

    if not applications:
        print("No applications available to search.")
        return

    while True:
        print("1. Search by Company Name")
        print("2. Search by Job Title")
        print("3. Search by Application Status")
        print("4. Search by Job Location")
        print("5. Search by Application ID")
        print("6. Return to Main Menu")
        print("===============================")

        choice = input("Select search option: ").strip()

        if choice == "6":
            print("Returning to Main Menu...")
            break

        search_fields = {
            "1": "company_name",
            "2": "job_title",
            "3": "application_status",
            "4": "job_location",
            "5": "application_id",
        }

        if choice not in search_fields:
            print("Invalid option. Please try again.")
            continue

        field = search_fields[choice]

        search_term = get_non_empty_text("Enter your search term: ").lower()

        matching_applications = []

        for application in applications:
            field_value = str(application[field]).lower()

            if choice == "5":
                if field_value == search_term:
                    matching_applications.append(application)

            elif search_term in field_value:
                matching_applications.append(application)

        if not matching_applications:
            print("No matching applications found.")

        else:
            print(f"Found {len(matching_applications)} matching application(s).")
            print("===============================")

            for application in matching_applications:
                print(f"Application ID: {application['application_id']}")
                print(f"Company: {application['company_name']}")
                print(f"Job Title: {application['job_title']}")
                print(f"Job Location: {application['job_location']}")
                print(f"Application Date: {application['application_date']}")
                print(f"Application Status: {application['application_status']}")

                interview_date = application["interview_date"]

                if not interview_date:
                    interview_date = "Not scheduled"

                print(f"Interview Date: {interview_date}")
                print(f"Applicant Name: {application['applicant_name']}")
                print(f"Contact Email: {application['contact_email']}")
                print(f"Phone Number: {application['phone_number']}")
                notes = application.get("notes", "")

                if not notes:
                    notes = "No notes available"

                print(f"Notes: {notes}")
                print("===============================")
