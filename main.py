from flask import Flask, request, jsonify, abort, make_response
import schedule, time, atexit, string, random
from json_file_helper import read_json, create_json, update_json, write_json, delete_json, reminder_json_exists
from dateutil.relativedelta import relativedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, date
from twilio.rest import Client
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
twilio_client = Client()


@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    reminders = read_json()
    return jsonify({'reminders': reminders})


@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    req_data = request.get_json()
    reminder = {
        'id': generate_reminder_id(),
        'phone_number': req_data['phone_number'],
        'message': req_data['message'],
        'interval': req_data['interval'],
        'due_date': req_data['due_date']
    }

    if reminder_json_exists():
        update_json(reminder)
    else:
        create_json(reminder)
    return jsonify({'reminder': reminder}), 201

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    reminders = read_json()
    reminder = [reminder for reminder in reminders if reminder['id'] == reminder_id]
    if len(reminder) == 0:
       abort(404)
    data = {}
    reminders.remove(reminder[0])
    data['reminders'] = reminders
    write_json(data)
    return jsonify({'message': 'Reminder has been removed successfully'})

def generate_reminder_id():
    reminders, reminders_length = read_json(), len(read_json())
    return reminders[-1]['id'] + 1 if reminders_length > 0 else 1
    
def find_reminders_due():
    reminders = read_json()
    reminders_due = [
        reminder for reminder in reminders if reminder['due_date'] == str(date.today())
    ]
    print(reminders_due)
    # return jsonify({ 'reminders': reminders_due})
    if len(reminders_due) > 0:
        send_whatsapp_reminder(reminders_due)


def send_whatsapp_reminder(reminders):
    for reminder in reminders:
        twilio_from = os.getenv("TWILIO_FROM")
        to_phone_number = reminder['phone_number']
        message = twilio_client.messages.create(
            body=reminder['message'],
            from_=f"whatsapp:{twilio_from}",
            to=f"whatsapp:{to_phone_number}")
        update_due_date(reminder)

def update_due_date(reminder):
    reminders = read_json();
    data = {}
    reminders.remove(reminder)
    new_due_date = datetime.strptime(reminder['due_date'], '%Y-%m-%d').date() + relativedelta(months=1)
    reminder['due_date'] = str(new_due_date)
    reminders.append(reminder)
    data['reminders'] = reminders
    write_json(data)



@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


# create schedule for sending reminders
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(func=find_reminders_due,
                  trigger=IntervalTrigger(seconds=40),
                  id='send_reminders_due_job',
                  name='Send WhatsApp Reminders',
                  replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run()