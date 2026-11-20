from datetime import date, datetime


def calculate_dashboard(applications):

    total_applications = len(applications)
    upcoming_interview_list = []

    applied = 0
    under_review = 0
    interview = 0
    offered = 0
    rejected = 0
    scheduled_interviews = 0
    upcoming_interviews = 0
    past_interviews = 0

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

        interview_date = application["interview_date"]

        if interview_date:
            scheduled_interviews += 1

            interview_date = date.fromisoformat(interview_date)

            if interview_date >= date.today():
                upcoming_interviews += 1

                days_remaining = (interview_date - date.today()).days

                upcoming_interview_list.append(
                    {
                        "company_name": application["company_name"],
                        "job_title": application["job_title"],
                        "interview_date": interview_date.strftime("%A, %d %B %Y"),
                        "application_id": application["application_id"],
                        "days_remaining": days_remaining,
                    }
                )

            else:
                past_interviews += 1

    if total_applications > 0:
        interview_rate = (interview / total_applications) * 100
        offer_rate = (offered / total_applications) * 100

    else:
        interview_rate = 0
        offer_rate = 0

    upcoming_interview_list.sort(key=lambda item: item["interview_date"])

    return {
        "total_applications": total_applications,
        "applied": applied,
        "under_review": under_review,
        "interview": interview,
        "offered": offered,
        "rejected": rejected,
        "scheduled_interviews": scheduled_interviews,
        "interview_rate": round(interview_rate, 2),
        "offer_rate": round(offer_rate, 2),
        "upcoming_interviews": upcoming_interviews,
        "past_interviews": past_interviews,
        "upcoming_interview_list": upcoming_interview_list,
    }
