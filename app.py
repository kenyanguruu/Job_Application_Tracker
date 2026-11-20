from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
from dashboard import calculate_dashboard
from storage import (
    save_application,
    load_applications,
    get_next_application_id,
    advance_application_id,
    save_all_applications,
    save_deleted_application,
)

app = Flask(__name__)
app.secret_key = "job-tracker-development-key"


@app.route("/applications")
def home():
    applications = load_applications()
    return render_template("index.html", applications=applications)


@app.route("/applications/status/<status>")
def status_applications(status):

    applications = load_applications()

    valid_statuses = ("Applied", "Under Review", "Interview", "Offered", "Rejected")

    if status not in valid_statuses:
        return "Invalid application status.", 404

    filtered_applications = [
        application
        for application in applications
        if application["application_status"] == status
    ]

    return render_template("index.html", applications=filtered_applications)


@app.route("/search")
def search_applications():

    query = request.args.get("query", "").strip().lower()

    applications = load_applications()

    if query:
        applications = [
            application
            for application in applications
            if query in application["company_name"].lower()
            or query in application["job_title"].lower()
            or query in application["application_status"].lower()
            or query in application["job_location"].lower()
            or query in application["application_id"].lower()
        ]

    return render_template("index.html", applications=applications)


@app.route("/application/<int:application_id>")
def application_details(application_id):

    applications = load_applications()

    for application in applications:
        if int(application["application_id"]) == application_id:
            return render_template("application_details.html", application=application)

    return "Application not found.", 404


@app.route("/application/<int:application_id>/edit")
def edit_application(application_id):

    applications = load_applications()

    for application in applications:
        if int(application["application_id"]) == application_id:
            return render_template("edit_application.html", application=application)

    return "Application not found.", 404


@app.route("/application/<int:application_id>/update", methods=["POST"])
def update_application(application_id):

    applications = load_applications()

    for application in applications:

        if int(application["application_id"]) == application_id:

            # Collect updated information
            company_name = request.form.get("company_name", "").strip()
            job_title = request.form.get("job_title", "").strip()
            job_location = request.form.get("job_location", "").strip()
            interview_date = request.form.get("interview_date", "").strip()
            application_status = request.form.get("application_status", "").strip()
            applicant_name = request.form.get("applicant_name", "").strip()
            contact_email = request.form.get("contact_email", "").strip().lower()
            phone_number = request.form.get("phone_number", "").strip()
            notes = request.form.get("notes", "").strip()

            # Validate required fields
            if not all(
                [
                    company_name,
                    job_title,
                    job_location,
                    application_status,
                    applicant_name,
                    contact_email,
                    phone_number,
                ]
            ):
                flash("Please complete all required fields.", "error")
                return redirect(
                    url_for("edit_application", application_id=application_id)
                )

            # Validate application status
            if application_status not in (
                "Applied",
                "Under Review",
                "Interview",
                "Offered",
                "Rejected",
            ):
                flash("Invalid application status.", "error")
                return redirect(
                    url_for("edit_application", application_id=application_id)
                )

            # Update the existing application
            application["company_name"] = company_name
            application["job_title"] = job_title
            application["job_location"] = job_location
            application["interview_date"] = interview_date
            application["application_status"] = application_status
            application["applicant_name"] = applicant_name
            application["contact_email"] = contact_email
            application["phone_number"] = phone_number
            application["notes"] = notes

            # Save all applications back to CSV
            save_all_applications(applications)

            flash("Application updated successfully!", "success")

            return redirect(
                url_for("application_details", application_id=application_id)
            )

    return "Application not found.", 404


@app.route("/application/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):

    applications = load_applications()

    for application in applications:

        if int(application["application_id"]) == application_id:

            # Archive the application first
            save_deleted_application(application)

            # Remove it from active applications
            applications.remove(application)

            # Save the remaining applications
            save_all_applications(applications)

            flash("Application deleted successfully!", "success")

            return redirect(url_for("home"))

    return "Application not found.", 404


@app.route("/add-application", methods=["POST"])
def add_application():

    company_name = request.form.get("company_name", "").strip()
    job_title = request.form.get("job_title", "").strip()
    job_location = request.form.get("job_location", "").strip()
    interview_date = request.form.get("interview_date", "").strip()
    application_status = request.form.get("application_status", "").strip()
    applicant_name = request.form.get("applicant_name", "").strip()
    contact_email = request.form.get("contact_email", "").strip().lower()
    phone_number = request.form.get("phone_number", "").strip()
    notes = request.form.get("notes", "").strip()

    if not all(
        [
            company_name,
            job_title,
            job_location,
            application_status,
            applicant_name,
            contact_email,
            phone_number,
        ]
    ):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("home"))

    if application_status not in (
        "Applied",
        "Under Review",
        "Interview",
        "Offered",
        "Rejected",
    ):
        flash("Invalid application status.", "error")
        return redirect(url_for("home"))

    application_id = get_next_application_id()

    application = {
        "application_id": application_id,
        "company_name": company_name,
        "job_title": job_title,
        "job_location": job_location,
        "application_date": date.today().isoformat(),
        "interview_date": interview_date,
        "application_status": application_status,
        "applicant_name": applicant_name,
        "contact_email": contact_email,
        "phone_number": phone_number,
        "notes": notes,
    }

    save_application(application)
    advance_application_id(application_id)

    flash("Application saved successfully!", "success")

    return redirect(url_for("home"))


@app.route("/about")
def about():
    return "This application helps me manage my job applications."


@app.route("/")
@app.route("/dashboard")
def dashboard():

    applications = load_applications()

    dashboard_data = calculate_dashboard(applications)

    return render_template("dashboard.html", dashboard=dashboard_data)


if __name__ == "__main__":
    app.run(debug=True)
