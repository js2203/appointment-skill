from mycroft import MycroftSkill, intent_file_handler
from datetime import datetime, timedelta, time
import json
import caldav
import os


def handle_event(event):
    event.load()
    e = event.instance.vevent
    try:
        event_location = e.location.value
    except AttributeError:
        event_location = 'Unknown'
    event_summary = e.summary.value

    if e.dtstart.value.strftime("%H:%M") == "00:00" and e.dtend.value.strftime("%H:%M") == "00:00":
        day = e.dtstart.value.strftime("%d %B, %Y")
        event_time = ("an allday event at {}".format(day))
    else:
        event_start = e.dtstart.value.strftime("%H:%M, %D")
        event_end = e.dtend.value.strftime("%H:%M, %D")
        event_time = ("a normal event from {} to {}".format(event_start, event_end))

    return {"event_time": event_time, "event_summary": event_summary, "event_location": event_location}


def sort_events(events):
    return events.dtstart.value.strftime("%D,%H:%M")


class Appointment(MycroftSkill):

    def __init__(self):
        MycroftSkill.__init__(self)
        try:
            with open((os.path.join(os.path.dirname(__file__), 'conf.json'))) as json_file:
                data = json.load(json_file)
                self.url = data['url']
                self.username = data['username']
                self.password = data['password']
        except ImportError:
            self.log.info(ImportError)

        self.client = caldav.DAVClient(url=self.url, username=self.username, password=self.password)
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()
        self.today = datetime

    @intent_file_handler('appointment.intent')
    def handle_appointment(self, message):

        event_array = []
        self.today = datetime.today()

        if len(self.calendars) > 0:
            calendar = self.calendars[0]
            events = calendar.date_search(self.today, end=None)
            for event in events:
                event.load()
                e = event.instance.vevent
                event_array.append(e)
            event_array.sort(key=sort_events)

        event_data = handle_event(events[0])

        self.speak_dialog('appointment', data={"date": event_data["event_time"], "summary": event_data["event_summary"],
                                               "location": event_data["event_location"]})


def create_skill():
    return Appointment()
