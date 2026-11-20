import applications
import dashboard


def welcome():
    print("======================================")
    print("JOB APPLICATION TRACKER")
    print("======================================")
    print("Welcome to the job application tracker.")
    print("======================================")


welcome()


def show_menu():
    while True:
        print("1. Add Job Application")
        print("2. View All Applications")
        print("3. Update Application")
        print("4. Delete Application")
        print("5. Search Applications")
        print("6. View Dashboard")
        print("7. Exit")
        print("======================================")

        choice = input("Select an option: ")
        if choice == "1":
            applications.add_application()
        elif choice == "2":
            applications.view_applications()
        elif choice == "3":
            applications.update_application()
        elif choice == "4":
            applications.delete_application()
        elif choice == "5":
            applications.search_applications()
        elif choice == "6":
            dashboard.show_dashboard()
        elif choice == "7":
            print("Thank you for using the Job Application Tracker!")
            print("Goodbye!")
            break
        else:
            print("Invalid option")

        print("======================================")


show_menu()
