import applications


def test_find_application_by_id(monkeypatch):
    sample_applications = [
        {
            "application_id": "101",
            "company_name": "Google",
            "job_title": "Python Developer",
        }
    ]

    monkeypatch.setattr(applications, "applications", sample_applications)

    result = applications.find_application_by_id(101)

    assert result == sample_applications[0]


def test_find_application_by_id_not_found(monkeypatch):
    sample_applications = []

    monkeypatch.setattr(applications, "applications", sample_applications)

    result = applications.find_application_by_id(999)

    assert result is None


def test_get_application_status_valid(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "interview")

    result = applications.get_application_status()

    assert result == "Interview"


def test_get_application_status_invalid(monkeypatch):
    user_inputs = iter(["Pending", "Applied"])

    monkeypatch.setattr("builtins.input", lambda prompt: next(user_inputs))

    result = applications.get_application_status()

    assert result == "Applied"
