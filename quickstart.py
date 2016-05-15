from __future__ import print_function
import os
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import httplib2
from model import db, Event, Calendar, User, UserCal, CalEvent
import datetime


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials.
    """

    home_dir = os.path.expanduser('~/Desktop/Hackbright/proj')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
    return credentials


def get_api_service():
    """Creates httplib2.Http object to handle http requests and authorizes it.

    Returns:
        An instance of an API service object that can be used to make API calls."""

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    return service


def main():

    service = get_api_service()

    user_id = 1  # would be passed from database/credentials

    calendarsResult = service.calendarList().list().execute()

    # next_sync_token = calendarsResult['nextSyncToken']
    # calendar_etags = calendarsResult['etag']

    user_exists = User.query.get(user_id)

    if user_exists is None:

        user = User(user_id=user_id)

        db.session.add(user)
        db.session.commit()

    calendars = calendarsResult.get('items', [])

    id_list = []

    for calendar in calendars:
        if 'selected' in calendar:

            calendar_id = calendar['id']
            timezone = calendar['timeZone']
            summary = calendar['summary']
            etag = calendar['etag']

            id_list.append(calendar_id)

            if 'primary' in calendar:
                primary = calendar['primary']
            else:
                primary = False

            # if 'selected' in calendar:
            #     selected = calendar['selected']
            # else:
            #     selected = False

            # if calendar_exists and calendar_exists.etag == etag:
            # else:

            cal_exists = Calendar.query.get(calendar_id)
            usercal_exists = UserCal.query.filter_by(user_id=user_id,
                                                     calendar_id=calendar_id).first()

            if cal_exists and usercal_exists is None:

                usercal = UserCal(user_id=user_id,
                                  calendar_id=calendar_id,
                                  primary=primary)

                # usercal.calendar_id = calendar_id

                db.session.add(usercal)
                db.session.commit()

            # elif cal_exists and cal_exists.etag != etag:
            #     update db

            elif cal_exists is None:

                calendar_obj = Calendar(calendar_id=calendar_id,
                                        etag=etag,
                                        summary=summary,
                                        timezone=timezone)

                db.session.add(calendar_obj)
                db.session.commit()

                usercal = UserCal(user_id=user_id,
                                  calendar_id=calendar_id,
                                  primary=primary)

                db.session.add(usercal)
                db.session.commit()

    # 'Z' indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    for id_ in id_list:  # for each calendar

        eventsResult = service.events().list(calendarId=id_,
                                             timeMin=now,
                                             maxResults=100,
                                             singleEvents=True,
                                             orderBy='startTime').execute()

        # events_etag = eventsResult['etag']
        # events_email = eventsResult['summary']
        # events_timezone = eventsResult['timeZone']
        # events_updated_at = eventsResult['updated']

        events = eventsResult.get('items', [])  # pulls events

        for event in events:

            etag = event['etag']
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['start'].get('date'))
            creator = event['creator'].get('email', [])
            # status = event['status']
            summary = event['summary']
            event_id = event['id']
            created_at = event['created']
            updated_at = event['updated']

            # if event is not already in database:
                # add event
                # add guest
            # else: (if event is in the database)
                # if we haven't looked @ their calendar before
                # add guest

            # if 'attendees' in event:
            #     attendees = event['attendees']
            # else:
            #     conf_rm = None

            # for attendee in attendees:
            #     if 'resource' in attendee:
            #         conf_rm = attendee['displayName']
            #         break
            #     else:
            #         conf_rm = None

            # event_exists in db
            event_exists = Event.query.get(event_id)
            calevents_exists = CalEvent.query.filter_by(calendar_id=id_,
                                                        event_id=event_id).first()

            if event_exists and calevents_exists is None:

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()

            # elif event_exists and event_exists.etag != etag:

            #     event_exists.etag = etag
            #     event_exists.creator = creator
            #     event_exists.start = start
            #     event_exists.end = end
            #     event_exists.created_at = created_at
            #     event_exists.updated_at = updated_at
            #     event_exists.summary = summary

            #     calevent = CalEvent(calendar_id=id_,
            #                         event_id=event_id,
            #                         status=status)

            #     db.session.add(calevent)
            #     db.session.commit()

            elif event_exists is None:

            # if 'attendees' in event:
            #     attendees = event['attendees']
            #     print(attendees)

            #     for attendee in attendees:
            #         if 'resource' in attendee:
            #             display_name = attendee['displayName']
            #             print(display_name)
            #         else:
            #             email = attendee['email']
            #             print(email)

                event_obj = Event(event_id=event_id,
                                  etag=etag,
                                  creator=creator,
                                  start=start,
                                  end=end,
                                  created_at=created_at,
                                  updated_at=updated_at,
                                  summary=summary)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id)

                db.session.add(calevent)
                db.session.commit()
