import os
from flask import Flask, request, jsonify, abort, make_response
from reminder_json_helper import read_reminder_json, create_reminder_json, update_reminder_json, write_reminder_json
import uuid
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__)
twilio_client = Client()


@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    reminders = read_reminder_json()
    return jsonify({'reminders': reminders})


@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    req_data = request.get_json()

    if not all(item in req_data
               for item in ("phone_number", "message", "due_date")):
        abort(400)

    reminder = {
        'id': uuid.uuid4().hex,
        'phone_number': req_data['phone_number'],
        'message': req_data['message'],
        'interval': 'monthly',
        'due_date': req_data['due_date']
    }

    create_reminder_json(reminder)
    return jsonify({'reminder': reminder}), 201


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@app.route('/api/reminders/<reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    reminders = read_reminder_json()
    reminder = [
        reminder for reminder in reminders if reminder['id'] == reminder_id
    ]
    if len(reminder) == 0:
        abort(404)
    reminders.remove(reminder[0])
    data = {}
    data['reminders'] = reminders
    write_reminder_json(data)
    return jsonify({'message': 'Reminder has been removed successfully'})


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


def find_reminders_due():
    reminders = read_reminder_json()
    reminders_due = [
        reminder for reminder in reminders
        if reminder['due_date'] == str(date.today())
    ]
    if len(reminders_due) > 0:
        send_sms_reminder(reminders_due)


def send_whatsapp_reminder(reminders):
    for reminder in reminders:
        twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
        to_phone_number = reminder['phone_number']
        message = twilio_client.messages.create(
            body=reminder['message'],
            from_=f"whatsapp:{twilio_from}",
            to=f"whatsapp:{to_phone_number}")
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


def send_sms_reminder(reminders):
    for reminder in reminders:
        twilio_from = os.getenv("TWILIO_SMS_FROM")
        to_phone_number = reminder['phone_number']
        message = twilio_client.messages.create(
            body=reminder['message'],
            from_=f"{twilio_from}",
            to=f"{to_phone_number}")
        update_due_date(reminder)


# create schedule for sending reminders
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=find_reminders_due,
                  trigger=IntervalTrigger(seconds=60),
                  id='send_reminders_due_job',
                  name='Send WhatsApp Reminders',
                  replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run()

