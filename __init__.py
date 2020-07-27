"""A one line summary of the module or program, terminated by a period.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

  Typical usage example:

  foo = ClassFoo()
  bar = foo.FunctionBar()
"""
import os
import json
from datetime import datetime, timedelta, time
import caldav
from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.parse import extract_datetime, normalize
from mycroft.util.format import nice_time, nice_date, nice_date_time
from mycroft.util.time import to_local, now_local


def handle_event(event):
    """Retrieves information from an event instance.

    Retrieves and handles information from an event instance if available.
    Also converts the starting and end time in a string.

    Args:
        event:
            A calendar event instances.
    Returns:
        A dictionary containing the time, summary and location
        of the event. For example:
        {"event_time": "01:12, 07.05.2020",
         "event_summary": "this is an event",
         "event_location": "home"}
    """
    try:
        event_location = event.location.value
    except AttributeError:
        event_location = 'Unknown'
    event_summary = event.summary.value

    if event.dtstart.value.strftime("%H:%M") == "00:00" \
            and event.dtend.value.strftime("%H:%M") == "00:00":
        day = event.dtstart.value.strftime("%d %B, %Y")
        event_time = ("an allday event at {}".format(day))
    else:
        event_start = event.dtstart.value.strftime("%H:%M, %D")
        event_end = event.dtend.value.strftime("%H:%M, %D")
        event_time = ("a normal event from {} to {}".format(event_start, event_end))

    return {"event_time": event_time, "event_summary": event_summary,
            "event_location": event_location}


def sort_events(event):
    """Returns the starting date of a calendar event instance.

    Returns the starting date of a calendar event instance, that
    a list of events can be sorted by starting dates.

    Args:
        event:
            A calendar event instances.
    Returns:
        A calendar event starting date.
    """
    return event.dtstart.value.strftime("%D,%H:%M")


class Appointment(MycroftSkill):
    """Summary of class here.

    Longer class information....
    Longer class information....

    Attributes:
        url:
        username:
        password:
        client:
        principal:
        calendars:
        today:
    """

    def __init__(self):
        """
        Args:
        Returns:
        """
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

    @intent_file_handler('next_appointment.intent')
    def handle_appointment_next(self):
        """Returns the next appointment in the calendar.

        If the correct intent is spoken by the user, all entries
        in the calendar with a start date in the future will be retrieved.
        The events are then sorted by date and the location, name and date
        of the event are spoken in the dialog by mycroft

        Args:
            self
        Returns:
            None
        """
        event_array = []
        self.today = datetime.today()

        if len(self.calendars) >= 0:
            calendar = self.calendars[0]
            # search for all events that happen in the future,
            # one could specify the end to reduce the load.
            events = calendar.date_search(self.today, end=None)
            for event in events:
                event.load()
                event_instance = event.instance.vevent
                # only add an event if it occurs at an later time than the query
                # not including already running events
                if event_instance.dtstart.value.strftime("%D, %H:%M") \
                        > self.today.strftime("%D, %H:%M"):
                    event_array.append(event_instance)
            # sort the events, because they are separated
            # in allday and normal events at first
            event_array.sort(key=sort_events)
        # the first event in the array is the next occurring
        event_data = handle_event(event_array[0])
        self.speak_dialog('next.appointment', data={"date": event_data["event_time"],
                                                    "summary": event_data["event_summary"],
                                                    "location": event_data["event_location"]})

    @intent_file_handler('create_appointment.intent')
    def handle_appointment_create(self, message):
        self.log.debug('create')
        name = message.data.get('name')
        while not name:
            name = self.get_response("new.event.name")

        start_date = self.get_time("new.event.date", datetime.now())

        if start_date.time() == time(0):
            all_day = self.ask_yesno('new.event.allday')
            if all_day == 'yes':
                end_date = (start_date + timedelta(days=1)),
            else:
                start_time = self.get_time("new.event.time", datetime.now())
                start_date = datetime.combine(start_date.date(), start_time.time())
                end_date = self.get_time("new.event.end", start_date)
        else:
            end_date = self.get_time("new.event.end", start_date)

        if len(self.calendars) >= 0:
            calendar = self.calendars[0]
            calendar.save_event("""BEGIN:VCALENDAR
                        VERSION:2.0
                        PRODID:SI2020js
                        BEGIN:VEVENT
                        UID:{}
                        DTSTAMP:{}
                        DTSTART:{}
                        DTEND:{}
                        SUMMARY:{}
                        END:VEVENT
                        END:VCALENDAR
                        """.format(self.username,
                                   datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                                   start_date.strftime("%Y%m%dT%H%M%SZ"),
                                   end_date.strftime("%Y%m%dT%H%M%SZ"),
                                   name))

        self.speak('Created {} from {} till {}'.format(name, start_date, end_date))

    @intent_file_handler('delete_appointment.intent')
    def handle_appointment_delete(self, message):
        self.log.debug('delete')
        name = message.data.get('name')
        while not name:
            name = self.get_response("new.event.name")

        if len(self.calendars) > 0:
            calendar = self.calendars[0]

        events = calendar.date_search(datetime.today())

        for event in events:
            event.load()
            e = event.instance.vevent
            summary: str = e.summary
            if summary.lower() == name:
                event.delete()
                self.speak("deleted " + e.summary)

    def get_time(self, dialog: str, start: datetime) -> datetime:
        spoken_date = None
        while spoken_date is None:
            try:
                utterance = self.get_response(dialog)
                spoken_date, rest = extract_datetime(utterance, start, self.lang)
            except TypeError:
                pass
        return spoken_date


def create_skill():
    """
    Args:
    Returns:
    """
    return Appointment()
