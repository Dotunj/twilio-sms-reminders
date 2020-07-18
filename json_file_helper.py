import os
import json

def read_json():
    if reminder_json_exists():
       with open('reminder.json', 'r') as reminder_json:
            data = json.load(reminder_json);
            return data['reminders']
    else: 
        return {}

def create_json(reminder):
    data = {}
    data['reminders'] = []
    data['reminders'].append(reminder)
    write_json(data)


def update_json(reminder):
    with open('reminder.json', 'r+') as reminder_json:
        data = json.load(reminder_json)
        reminders = data['reminders']
        reminders.append(reminder)
        write_json(data)

def write_json(data, filename='reminder.json'):
    with open(filename, 'w+') as outfile:
        json.dump(data, outfile, indent=4)

def delete_json(reminders):
    data = {}
    data['reminders'] = reminders
    write_json(data)

def reminder_json_exists():
    return os.path.isfile('reminder.json')
