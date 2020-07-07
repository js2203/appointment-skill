from mycroft import MycroftSkill, intent_file_handler
from datetime import datetime, timedelta, time
import json
import caldav


class Appointment(MycroftSkill):

    calendars, today, principal, client = None, None, None, None
    url = 'https://next.social-robot.info/nc/remote.php/dav'
    username, password = '', ''

    def __init__(self):
        MycroftSkill.__init__(self)
        try:
            with open('conf.txt') as json_file:
                data = json.load(json_file)
                self.url = data['URL']
                self.username = data['username']
                self.password = data['password']
        except ImportError:
            print(ImportError)

        self.today = datetime.combine(datetime.today(), time(0, 0))
        self.client = caldav.DAVClient(url=self.url, username=self.username, password=self.password)
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()

    def handleEvent(self, event):
        event.load()
        e = event.instance.vevent
        try:
            eventLocation = e.location.value
        except AttributeError:
            eventLocation = 'Unknown Location'
        eventSummary = e.summary.value

        if e.dtstart.value.strftime("%H:%M") == "00:00":
            eventTime = e.dtstart.value.strftime("%d %B, %Y")
        else:
            eventTime = e.dtstart.value.strftime("%d %B, %Y at %H:%M")

        return {"eventTime": eventTime, "eventSummary": eventSummary, "eventSummary": e.summary.value}

    @intent_file_handler('appointment.intent')
    def handle_appointment(self, message):

        if len(self.calendars) > 0:
            calendar = self.calendars[0]
            events = calendar.date_search(self.today, end=None)

        event_data = self.handleEvent(events[0])

        self.speak_dialog('appointment', data={"date": event_data["eventTime"],"summary": event_data["eventSummary"], "location": event_data["eventSummary"]})


def create_skill():
    return Appointment()

