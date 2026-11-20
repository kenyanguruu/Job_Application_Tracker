# Job Application Tracker

## Project Overview

The Job Application Tracker is a Python-based command-line application designed to help job seekers manage and monitor their job applications.

It allows users to record job applications, update application details, search for applications, track application statuses, and view application statistics through a dashboard.

The application uses CSV files to store application records, making it simple to manage data without requiring a database.

## Features

- Add new job applications.
- View all recorded job applications.
- Update existing application details.
- Delete job applications.
- Archive deleted applications.
- Search applications by:
  - Company name
  - Job title
  - Application status
  - Job location
  - Application ID
- Track application statuses.
- Record interview dates.
- Store applicant contact information.
- Add optional notes to applications.
- View application statistics through a dashboard.
- Automatically generate application IDs.
- Validate user input.
- Store application records using CSV files.

## Technologies Used

- Python 3
- CSV module
- OS module
- Datetime module
- Pytest (automated testing, to be completed)
- Git and GitHub

## Project Structure

```text
Job_Application_Tracker/
│
├── applications.py
├── dashboard.py
├── main.py
├── storage.py
├── README.md
│
├── data/
│   ├── applications.csv
│   ├── applications_backup.csv
│   ├── deleted_applications.csv
│   ├── next_application_id.txt
│   └── backup files
│
└── tests/
    └── test_applications.py
```

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate into the project folder

```bash
cd Job_Application_Tracker
```

### 3. Make sure Python is installed

Check your Python version:

```bash
python --version
```

### 4. Run the application

```bash
python main.py
```

## How to Use

After starting the application, the main menu displays the following options:

1. Add Job Application
2. View All Applications
3. Update Application
4. Delete Application
5. Search Applications
6. View Dashboard
7. Exit

### Add Job Application

Enter the requested information, including company name, job title, location, application status, contact information, and optional notes.

The application automatically generates a unique application ID.

### View All Applications

Displays all active job applications and their recorded information.

### Update Application

Allows users to update existing application details, including company information, application status, interview date, contact information, and notes.

### Delete Job Application

Allows users to remove an application from active records.

A copy of the deleted application is saved in the deleted applications archive.

### Search Applications

Users can search for applications using company name, job title, application status, job location, or application ID.

### View Dashboard

Displays statistics about recorded applications, including:

- Total applications
- Applications by status
- Interview statistics
- Interview rate
- Offer rate
- Scheduled interviews

### Exit

Closes the application.

## Data Storage

The application uses CSV files to store job application records.

- `applications.csv` stores active applications.
- `deleted_applications.csv` stores archived applications.
- `next_application_id.txt` helps maintain application ID numbering.

CSV storage makes the application easy to use and does not require a database server.

## Testing

The project includes a `tests/` directory for automated tests using pytest.

Run the tests with:

```bash
python -m pytest
```

## Future Improvements

- Migrate CSV storage to an SQLite database.
- Build a web application using Flask.
- Add HTML and CSS for the user interface.
- Improve automated test coverage.
- Add more advanced application analytics.

## Author

Job Application Tracker Project

## License

This project is intended for educational and personal development purposes.
