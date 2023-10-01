import streamlit as st
from datetime import datetime
import pandas as pd
import schedule
import pytz
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define the allowed usernames and passwords (replace with your credentials)
allowed_users = {
    "user1": "password1",
    "user2": "password2",
    "user3": "password3"
}

# Initialize a dictionary to store user timetables
user_timetables = {}

# Define a set to track sent email notifications for class reminders
sent_notifications = set()

# Define a set to track sent trial notification emails
sent_trial_notifications = set()

# Define a set to track sent custom reminder emails
sent_custom_reminders = set()

# Function to check if the provided username and password are valid
def authenticate(username, password):
    return allowed_users.get(username) == password

# Function to display the login page
def login():
    st.title("Login Page")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.user_info = username
            st.rerun() # Rerun the app to go to the main app page
        else:
            st.error("Invalid username or password")

# Function to schedule class email notifications
def schedule_class_email_notifications(class_name, day, time_slot, user_email):
    # Check if the class email notification has already been sent for this class and time slot
    notification_key = f"{class_name}-{day}-{time_slot}"
    if notification_key in sent_notifications:
        return

    def send_email_notification():
        smtp_server = 'smtp.gmail.com'  # Replace with your SMTP server address
        smtp_port = 587  # Replace with your SMTP server port
        sender_email = 'vitbhopal.classreminder@gmail.com'  # Replace with your sender email
        sender_password = 'bqum sydg ujdn ckni'  # Replace with your sender email password

        receiver_email = user_email  # User's email for receiving notifications

        subject = "Class Reminder"
        body = f"Your {class_name} class is starting in 5 minutes!"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()

        # Add the notification to the sent_notifications set
        sent_notifications.add(notification_key)

    # Parse the start time of the class
    class_start_time = pd.to_datetime(time_slot.split("-")[0].strip())
    class_start_time -= pd.Timedelta(hours=5,minutes=35)  # 5 minutes before class starts

    # Schedule the email notification to be sent just before the class
    schedule.every().day.at(class_start_time.strftime("%H:%M")).do(send_email_notification)

# Function to display the main app content
def main_app():
    st.title("Class Reminder App")

    # Define the days of the week and time slots here
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    time_slots = ["08:30 AM - 10:00 AM", "10:05 AM - 11:35 AM", "11:40 AM - 12:45 PM", "12:50 PM - 01:10 PM",
                  "01:15 PM - 02:45 PM", "02:50 PM - 04:20 PM", "04:25 PM - 05:55 PM", "06:00 PM - 07:30 PM"]

    # Get the user's email address
    user_email = st.text_input("Enter your email address:")

    # Get or create the user's timetable
    user_timetable = user_timetables.get(st.session_state.user_info, None)
    if user_timetable is None:
        user_timetable = pd.DataFrame("", columns=time_slots, index=days_of_week)
        user_timetables[st.session_state.user_info] = user_timetable

        # Button to send a trial notification email
        if st.button("Send Trial Notification"):
            if user_email:
                send_trial_notification(user_email)
                st.success(f"Trial notification sent to {user_email}")
            else:
                st.warning("Please enter your email address before sending a trial notification.")

        # Display a clock showing the current time
        delhi_timezone = pytz.timezone('Asia/Kolkata')
        delhi_time = datetime.now(delhi_timezone)
        current_time = delhi_time.strftime("%H:%M")
        st.subheader("Current Time:")
        st.write(current_time)

        # Option to send a custom reminder
        st.subheader("Send Custom Reminder:")
        custom_time = st.text_input("Enter the time (24-hour format, e.g., 14:30):")
        custom_message = st.text_input("Enter your custom reminder message:")
        if st.button("Send Custom Reminder"):
            if custom_time and custom_message:
                send_custom_reminder(user_email, custom_time, custom_message)
                st.success(f"Custom reminder scheduled for {custom_time}: {custom_message}")
            else:
                st.warning("Please fill in both time and reminder message fields.")

        # You can access the logged-in user using st.session_state.user_info
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        time_slots = ["08:30 AM - 10:00 AM", "10:05 AM - 11:35 AM", "11:40 AM - 12:45 PM", "12:50 PM - 01:10 PM",
                      "01:15 PM - 02:45 PM", "02:50 PM - 04:20 PM", "04:25 PM - 05:55 PM", "06:00 PM - 07:30 PM"]

        # Create a session state to store the class slot list and the timetable
        if 'to_do_class' not in st.session_state:
            st.session_state.to_do_class = []
        if 'timetable' not in st.session_state:
            st.session_state.timetable = pd.DataFrame("", columns=time_slots, index=days_of_week)

        # Input fields to add new class slots: Class name, class address, day of the week, and time slot
        new_class_name = st.text_input("Add New Course:")
        new_class_address = st.text_input("Class No.:")
        new_day = st.selectbox("Select a day of the week:", days_of_week)
        new_time_slot = st.selectbox("Select a time slot:", time_slots)

        # Function to check if a class slot with the same day and time slot already exists
        def class_slot_exists(class_name, day, time_slot):
            for item in st.session_state.to_do_class:
                if item[2] == day and item[3] == time_slot:
                    return True
            return False

        # Add a class slot
        if st.button("Add"):
            if new_class_name and new_class_address and new_day and new_time_slot:
                if not class_slot_exists(new_class_name, new_day, new_time_slot):
                    st.session_state.to_do_class.append((new_class_name, new_class_address, new_day, new_time_slot))
                    # Check if the selected time slot exists in the timetable columns before marking it with class name
                    if new_time_slot in st.session_state.timetable.columns:
                        st.session_state.timetable.loc[new_day, new_time_slot] = new_class_name
                else:
                    st.warning("A class slot with the same day and time slot already exists.")
            else:
                st.warning("Please fill in all fields before adding a class slot.")

        # Display the timetable with selected class slot names and highlight the selected slot in black
        st.subheader("Class Timetable:")
        if len(st.session_state.to_do_class) == 0:
            # Display an empty timetable
            st.write(st.session_state.timetable)
        else:
            def highlight_selected_slot(val):
                if val == new_class_name:  # Highlight the cell corresponding to the selected slot
                    return 'background-color: black; color: white;'
                return ''

            st.dataframe(st.session_state.timetable.style.applymap(highlight_selected_slot))

        # Display the list of class slots entered
        st.subheader("List of Class Slots Entered:")
        if len(st.session_state.to_do_class) == 0:
            st.write("No class slots entered.")
        else:
            for i, (class_name, class_address, day, time_slot) in enumerate(st.session_state.to_do_class):
                st.write(f"{i + 1}. {class_name} (Address: {class_address}, Day: {day}, Time Slot: {time_slot})")

        # Checkbox to mark classes as completed
        completed_class = st.checkbox("Mark class as completed")

        # Select a class to mark as completed
        if completed_class:
            class_to_complete = st.selectbox("Select a class to mark as completed",
                                             [
                                                 f"{class_name} (Address: {class_address}, Day: {day}, Time Slot: {time_slot})"
                                                 for class_name, class_address, day, time_slot in
                                                 st.session_state.to_do_class])
            if st.button("Complete Class"):
                # Find the class name within the selected string
                class_name_start = class_to_complete.find("(")
                if class_name_start != -1:
                    class_name = class_to_complete[:class_name_start].strip()
                    st.session_state.to_do_class = [(name, addr, day, slot) for name, addr, day, slot in
                                                    st.session_state.to_do_class if
                                                    f"{name} (Address: {addr}, Day: {day}, Time Slot: {slot})" != class_to_complete]
                    # Unmark the corresponding slot in the timetable
                    day, time_slot = [item[2:] for item in class_to_complete.split()[-4:-2]]
                    if time_slot in st.session_state.timetable.columns:
                        st.session_state.timetable.loc[day, time_slot] = ""
                    st.success(f"Class '{class_name}' marked as completed!")

    # Add a logout button
    if st.button("Logout"):
        st.session_state.user_info = None  # Clear the user's session state
        st.rerun()  # Rerun the app to go back to the login page

# Function to send a trial notification email
def send_trial_notification(user_email):
    # Check if the trial notification has already been sent
    if user_email in sent_trial_notifications:
        return

    smtp_server = "smtp.gmail.com"  # Replace with your SMTP server address
    smtp_port = 587  # Replace with your SMTP server port
    sender_email = 'vitbhopal.classreminder@gmail.com'  # Replace with your sender email
    sender_password = 'bqum sydg ujdn ckni'  # Replace with your sender email password

    receiver_email = user_email  # User's email for receiving notifications

    subject = "Trial Notification"
    body = "This is a trial notification message."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()

    # Add the user to the sent_trial_notifications set to mark it as sent
    sent_trial_notifications.add(user_email)

# Function to send a custom reminder
def send_custom_reminder(user_email, custom_time, custom_message):
    # Check if the custom reminder has already been sent for this user
    if user_email in sent_custom_reminders:
        return

    def send_email_notification():
        smtp_server = 'smtp.gmail.com'  # Replace with your SMTP server address
        smtp_port = 587  # Replace with your SMTP server port
        sender_email = 'vitbhopal.classreminder@gmail.com'  # Replace with your sender email
        sender_password = 'bqum sydg ujdn ckni'  # Replace with your sender email password

        receiver_email = user_email  # User's email for receiving notifications

        subject = "Custom Reminder"
        body = custom_message

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()

        # Add the user to the sent_custom_reminders set to mark it as sent
        sent_custom_reminders.add(user_email)


    # Parse the custom_time string into a datetime object
    custom_time_dt = datetime.strptime(custom_time, "%H:%M")
    custom_time_dt += pd.Timedelta(hours=5,minutes=30)

    # Schedule the custom reminder at the specified time
    schedule.every().day.at(custom_time_dt.strftime("%H:%M:%S")).do(send_email_notification)

# Check if the user is logged in
if __name__ == "__main__":
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

    if st.session_state.user_info is None:
        if login():
            st.button("Go to Main App")  # Add a button to navigate to the main app
    else:
        main_app()  # Display the main app content when logged in

# Start the scheduled tasks in the background
while True:
    schedule.run_pending()
    time.sleep(1)
