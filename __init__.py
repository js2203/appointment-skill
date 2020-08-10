"""A Mycroft-Skill to create, retrieve, delete calendar entries

This module contains a Mycroft-Skill class to work with a calendar.
For this module, a json file containing the url, username and
password for the calendar is required. This json has to be called
conf.json and should be located next to the __init__.py file.

Typical usage example:

appointment_skill = create_skill()
appointment_skill.handle_appointment_next(message)
appointment_skill.handle_appointment_delete(message)
appointment_skill.handle_appointment_list_day(message)
appointment_skill.handle_appointment_rename(message)
"""
import os
import json
from datetime import datetime, timedelta, time
import caldav
import vobject
from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.parse import extract_datetime


class Appointment(MycroftSkill):
    """Class to create, retrieve, delete calendar entries

    Attributes:
        url:
            primary CalDAV address
        username:
            username used to login in the calendar
        password:
            password used to login in the calendar
        client:
            A DAVClient object
        principal:
            A principal resource holds user-specific information
        calendars:
            all calendars owned by the principal
    """

    def __init__(self):
        """initializes all important variables when the class is created

        When the class is created, retrieves user credentials from the conf.json
        file and initializes the CalDAV client with the credentials.

        """
        MycroftSkill.__init__(self)
        try:
            with open((os.path.join(os.path.dirname(__file__),
                                    'conf.json'))) as json_file:
                data = json.load(json_file)
                self.url = data['url']
                self.username = data['username']
                self.password = data['password']
        except ImportError:
            self.log.info(ImportError)

        self.client = caldav.DAVClient(url=self.url,
                                       username=self.username,
                                       password=self.password)
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()

    @intent_file_handler('next_event.intent')
    def handle_appointment_next(self):
        """Tells the user the next appointment in the calendar.

        If the correct intent is spoken by the user, all entries
        in the calendar with a start date in the future will be retrieved.
        The events are then sorted by date and the location, name and date
        of the event are spoken in the dialog by mycroft.

        Returns:
            None
        """
        self.log.info('next')
        event_array = []
        if len(self.calendars) > 0:
            calendar = self.calendars[0]
            # search for all events that happen in the future
            events = calendar.date_search(datetime.now(), end=None)
            for event in events:
                event.load()
                event_instance = event.instance.vevent
                # not including already running events
                if event_instance.dtstart.value.strftime('%D, %H:%M') \
                        > datetime.today().strftime('%D, %H:%M'):
                    event_array.append(event_instance)
            # sort the events, because they are separated
            # in all-day and normal events at first
            event_array.sort(key=self.sort_events)
        # the first event in the array is the next occurring
        event_data = self.handle_event(event_array[0])
        self.speak_dialog('next.event',
                          data={'date': event_data['event_time'],
                                'summary': event_data['event_summary'],
                                'location': event_data['event_location']})

    @intent_file_handler('create_event.intent')
    def handle_appointment_create(self, message):
        """Creates a new event/ appointment in the calendar.

        Sequentially asks the user for the name, date and duration
        of the new event. As soon as all information is collected,
        builds a icalendar object with the information and pushes
        it to the calendar.

        Args:
            message:
                the spoken sentence by the user, which triggered this function.
        Returns:
            None
        """
        self.log.info('create')
        name = self.get_data(message, 'name', 'get.event.name')
        start_date = self.get_time('new.event.date',
                                   datetime.now(),
                                   message.data['utterance'])
        # if the time is 00:00, check if the user forgot to give a time
        if start_date.time() == time(0):
            all_day = self.ask_yesno('new.event.allday')
            if all_day == 'yes':
                end_date = start_date + timedelta(days=1)
            else:
                start_time = self.get_time('new.event.time',
                                           datetime.now())
                start_date = datetime.combine(start_date.date(),
                                              start_time.time())
                end_date = self.get_time('new.event.end', start_date)
        else:
            end_date = self.get_time('new.event.end', start_date)
        calendar = self.calendars[0]
        # builds correct iCal string serialization
        cal = vobject.iCalendar()
        cal.add('vevent')
        cal.vevent.add('summary').value = str(name)
        cal.vevent.add('dtstart').value = start_date
        cal.vevent.add('dtend').value = end_date
        calendar.add_event(str(cal.serialize()))
        self.speak_dialog('new.event.create',
                          data={'name': name,
                                'start': start_date.strftime('%D, %H:%M'),
                                'end': end_date.strftime('%D, %H:%M')})

    @intent_file_handler('delete_event.intent')
    def handle_appointment_delete(self, message):
        """deletes a calendar entry from the calendar

        Checks if an event with the name given by the user exists in the
        calendar. If a match is found, the user has to confirm that the
        event is the correct one. After a positive response, it deletes
        the event from the calendar. In case that it couldn't find a
        matching event, it tells the user that it couldn't find a match.

        Args:
            message:
                the spoken sentence by the user, which triggered this function.
        Returns:
            None
        """
        self.log.info('delete')
        name = self.get_data(message, 'name', 'get.event.name')
        try:
            target_events = self.get_event_by_name(name, datetime.now())
            if target_events:
                for event in target_events:
                    check_name = event.load().instance.vevent.summary.value
                    check_date = event.load().instance.vevent.dtstart.value
                    check_date = check_date.strftime('%D, %H:%M')
                    name_correct = self.ask_yesno('new.event.name.correct',
                                                  data={'name': check_name,
                                                        'date': check_date})
                    if name_correct == 'yes':
                        event.delete()
                        self.speak('deleted the event {}'.format(name))
                        break
                    if target_events.index(event) == len(target_events)-1:
                        self.speak('No more events with that name')
            else:
                self.speak_dialog('get.event.not.found',
                                  data={'name': name})
        except AttributeError:
            self.speak_dialog('get.event.not.found',
                              data={'name': name})

    @intent_file_handler('rename_event.intent')
    def handle_appointment_rename(self, message):
        """Changes the name of an existing event to a new one

        Checks if an event with the name given by the user exists in the
        calendar. If so, changes the old name to the new name spoken by
        the user after a confirmation. n case that it couldn't find a
        matching event, it tells the user that it couldn't find a match.

        Args:
            message:
                the spoken sentence by the user, which triggered this
                function.
        Returns:
            None
        """
        self.log.info('rename')
        name = self.get_data(message, 'name', 'get.event.name')
        try:
            target_events = self.get_event_by_name(name, datetime.now())
            if target_events:
                for event in target_events:
                    check_name = event.instance.vevent.summary.value
                    check_date = event.instance.vevent.dtstart.value
                    event_correct = self.ask_yesno('get.event.name.correct',
                                                   data={'name': check_name,
                                                         'date': check_date})
                    if event_correct == 'yes':
                        while True:
                            new_name = self.get_data(message, 'new_name',
                                                     'new.event.name')
                            correct = self.ask_yesno('new.event.name.correct',
                                                     data={'name': new_name})
                            if correct == 'yes':
                                break
                        event.instance.vevent.summary.value = new_name
                        event.save()
                        self.speak_dialog('get.event.name.change',
                                          data={'name_old': name,
                                                'name_new': new_name})
                        break
                    if target_events.index(event) == len(target_events)-1:
                        self.speak('No more events with that name')
            else:
                self.speak_dialog('get.event.not.found',
                                  data={'name': name})
        except AttributeError:
            self.speak_dialog('get.event.not.found',
                              data={'name': name})

    @intent_file_handler('day_event.intent')
    def handle_appointment_list_day(self, message):
        """list all events/ appointments on a specific day

        Asks the user for a date and returns all events happening on this
        day.

        Args:
            message:
                the spoken sentence by the user, which triggered this function.
        Returns:
            None
        """
        self.log.info('day')
        start_date = self.get_time('get.event.date',
                                   datetime.now(),
                                   message.data['utterance'])
        if not start_date:
            start_date = self.get_time('new.event.time', datetime.now())
        events = self.get_events_day(start_date.date(),
                                     start_date.date() + timedelta(days=1))
        for event in events:
            summary = event.summary.value
            start = event.dtstart.value.strftime('%D, %H:%M')
            end = event.dtend.value.strftime('%D, %H:%M')
            self.speak_dialog('list.event',
                              data={'name': summary,
                                    'start': start,
                                    'end': end})
        if not events:
            self.speak_dialog('get.event.not.found.day')

    def get_data(self, message, data: str, dialog: str) -> str:
        """retrieves information from the user.

        First it tries to retrieve a specific information from an intent
        message. If unable to do so, speaks a given dialog and returns the
        message from the user.

        Args:
            message:
                sentence spoken by the user.
            data:
                name of the variable specified in the intent.
            dialog:
                reference to the dialog, with which the user should be asked.
        Returns:
            information about a topic as string.
            For example: the name of an event
        """
        response = message.data.get(data)
        while not response:
            response = self.get_response(dialog)
        return response

    def get_time(self, dialog: str, start: datetime, message=None) -> datetime:
        """filters and returns the date and time in a message string.

        Tries to filter the date and time from a message string. If no
        date can be retrieved from the string, it asks the user for a date
        until one can be retrieved from the message.

        Args:
            dialog:
                name of the .dialog file, which should be used for asking
            start:
                date as datetime object, for reference if user uses
                relative time
            message:
                message as string
        Returns:
            datetime object with the date retrieved from the user
        """
        spoken_date = None
        try:
            spoken_date, rest = extract_datetime(message, start, self.lang)
        except TypeError:
            pass
        except ValueError:
            pass
        except AttributeError:
            pass
        while spoken_date is None:
            try:
                utterance = self.get_response(dialog)
                spoken_date, rest = extract_datetime(utterance,
                                                     start,
                                                     self.lang)
            except TypeError:
                pass
            except ValueError:
                pass
        return spoken_date

    def get_events_day(self, search_date: datetime, end=None) -> list:
        """Returns all events in a calendar on a specific day.

        Retrieves all events on a given date in the calendar
        and returns them loaded as vevent objects in a list.

        Args:
            search_date:
                date as datetime object for which all events should
                be returned.
            end:
        Returns:
            list with all events on the given date as vevent objects.
        """
        calendar = None
        if len(self.calendars) > 0:
            calendar = self.calendars[0]
        events = calendar.date_search(search_date.date(), end)
        all_events = []
        for event in events:
            event.load()
            all_events.append(event.instance.vevent)
        return all_events

    def get_event_by_name(self, name: str, search_date: datetime,
                          calendar=None) -> list:
        """searches for a specific event by name.

        Iterates through all events in the calendar until
        the event with the name given in arguments is found.

        Args:
            name:
                name of the desired event as string
            search_date:
                date as datetime object when the event takes place to
                reduce iterations, if no date is known use datetime.now()
                or datetime.today().
            calendar:
        Returns:
            event:
                vevent with the name given in args.
        """

        if len(self.calendars) > 0:
            calendar = self.calendars[0]
        events = calendar.date_search(search_date)
        event_list = []
        for event in events:
            event.load()
            event_instance = event.instance.vevent
            summary: str = event_instance.summary.value
            if summary.lower() == name.lower():
                event_list.append(event)
        return event_list

    @staticmethod
    def handle_event(event):
        """Retrieves information from an event instance.

        Retrieves and cleans up information from an vevent instance,
        if the information is available. Also converts the starting
        and end time in a string.

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

        if event.dtstart.value.strftime('%H:%M') == '00:00' \
                and event.dtend.value.strftime('%H:%M') == '00:00':
            day = event.dtstart.value.strftime('%d %B, %Y')
            event_time = ('an allday event at {}'.format(day))
        else:
            event_start = event.dtstart.value.strftime('%H:%M, %D')
            event_end = event.dtend.value.strftime('%H:%M, %D')
            event_time = ('a normal event from {} to {}'.format(event_start,
                                                                event_end))

        return {'event_time': event_time, 'event_summary': event_summary,
                'event_location': event_location}

    @staticmethod
    def sort_events(event):
        """Returns the starting date of a calendar event instance.

        Returns the starting date of a calendar vevent instance. Used that
        a list of events can be sorted by starting date.

        Args:
            event:
                A calendar event instances.
        Returns:
            A calendar event starting date.
        """
        return event.dtstart.value.strftime('%D,%H:%M')


def create_skill():
    """used by mycroft to create and load the skill
    """
    return Appointment()
