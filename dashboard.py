from applications import applications


def show_dashboard():
    print("======================================")
    print("JOB APPLICATION TRACKER DASHBOARD")
    print("======================================")

    total_applications = len(applications)

    print(f"Total Applications: {total_applications}")
    applied = 0
    under_review = 0
    interview = 0
    offered = 0
    rejected = 0

    for application in applications:
        status = application["application_status"]

        if status == "Applied":
            applied += 1

        elif status == "Under Review":
            under_review += 1

        elif status == "Interview":
            interview += 1

        elif status == "Offered":
            offered += 1

        elif status == "Rejected":
            rejected += 1

    print("===============================")
    print("APPLICATIONS BY STATUS")
    print("===============================")
    print(f"Applied: {applied}")
    print(f"Under Review: {under_review}")
    print(f"Interview: {interview}")
    print(f"Offered: {offered}")
    print(f"Rejected: {rejected}")

    if total_applications > 0:
        interview_rate = (interview / total_applications) * 100
        offer_rate = (offered / total_applications) * 100
    else:
        interview_rate = 0
        offer_rate = 0

    print("===============================")
    print("APPLICATION PERFORMANCE")
    print("===============================")
    print(f"Interview Rate: {interview_rate:.2f}%")
    print(f"Offer Rate: {offer_rate:.2f}%")

    scheduled_interviews = 0

    for application in applications:
        if application["interview_date"]:
            scheduled_interviews += 1

    print("===============================")
    print("INTERVIEW SCHEDULE")
    print("===============================")
    print(f"Scheduled Interviews: {scheduled_interviews}")
