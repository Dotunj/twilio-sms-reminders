import os
from reminder_json_helper import read_reminder_json, write_reminder_json
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

twilio_client = Client()


def find_reminders_due():
    reminders = read_reminder_json()
    reminders_due = [
        reminder for reminder in reminders
        if reminder['due_date'] == str(date.today())
    ]
    if len(reminders_due) > 0:
        send_sms_reminder(reminders_due)

def send_sms_reminder(reminders):
    for reminder in reminders:
        print('sending reminder')
        twilio_from = os.getenv("TWILIO_SMS_FROM")
        to_phone_number = reminder['phone_number']
        twilio_client.messages.create(
            body=reminder['message'],
            from_=f"{twilio_from}",
            to=f"{to_phone_number}")
        update_due_date(reminder)

def update_due_date(reminder):
    reminders = read_reminder_json()
    data = {}
    reminders.remove(reminder)
    new_due_date = datetime.strptime(
        reminder['due_date'], '%Y-%m-%d').date() + relativedelta(months=1)
    reminder['due_date'] = str(new_due_date)
    reminders.append(reminder)
    data['reminders'] = reminders
    write_reminder_json(data)

find_reminders_due()
    