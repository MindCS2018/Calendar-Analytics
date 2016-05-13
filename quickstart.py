from __future__ import print_function
import httplib2
import os

from model import connect_to_db, db, Event, Calendar, User, UserCal, CalEvent
# from server import app
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
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

        # Needed only for compatibility with Python 2.6
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    """"""

    # calls get_credentials function
    credentials = get_credentials()

    # would be passed from database/credentials
    user_id = 1

    # Creates an httplib2.Http object to handle HTTP requests and authorizes it
    http = credentials.authorize(httplib2.Http())

    # Returns an instance of an API service object that can be used to make API calls.
    service = discovery.build('calendar', 'v3', http=http)

    # 'Z' indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    calendarsResult = service.calendarList().list().execute()

    calendars_kind = calendarsResult['kind']
    next_sync_token = calendarsResult['nextSyncToken']
    etag = calendarsResult['etag']

    calendars = calendarsResult.get('items', [])
    id_list = []

    if not calendars:
        print ("No calendars found.")

    for calendar in calendars:
        calendar_id = calendar['id']
        timezone = calendar['timeZone']
        summary = calendar['summary']

        if 'primary' in calendar:
            primary = calendar['primary']
        else:
            primary = False

        if 'selected' in calendar:
            selected = calendar['selected']
            id_list.append(calendar_id)
        else:
            selected = False
        if 'description' in calendar:
            description = calendar['description']
        else:
            description = None

        # if calendar_exists and calendar_exists.etag == etag:
        #     continue
        # else:

        cal_exists = Calendar.query.get(calendar_id)

        if cal_exists:

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            # usercal.calendar_id = calendar_id

            db.session.add(usercal)
            db.session.commit()

        # elif cal_exists and cal_exists.etag != etag:
        #     update db

        else:

            calendar = Calendar(calendar_id=calendar_id,
                                etag=etag,
                                summary=summary,
                                description=description,
                                timezone=timezone)

            db.session.add(calendar)
            db.session.commit()

            usercal = UserCal(user_id=user_id,
                              calendar_id=calendar_id,
                              primary=primary,
                              selected=selected)

            db.session.add(usercal)
            db.session.commit()

    for id_ in id_list:

        eventsResult = service.events().list(calendarId=id_,
                                             timeMin=now,
                                             maxResults=100,
                                             singleEvents=True,
                                             orderBy='startTime').execute()

        events_etag = eventsResult['etag']
        events_kind = eventsResult['kind']
        events_email = eventsResult['summary']
        events_timezone = eventsResult['timeZone']
        events_updated_at = eventsResult['updated']

        events = eventsResult.get('items', [])

        # if empty list, print no upcoming events
        if not events:
            print('No upcoming events found.')

        # for each event dictionary in the events list
        for event in events:

            etag = event['etag']
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['start'].get('date'))
            creator = event['creator'].get('email', [])
            created = event['created']
            kind = event['kind']
            status = event['status']
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

            event_exists = Event.query.get(event_id)

            if event_exists:

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id,
                                    status=status)

                db.session.add(calevent)
                db.session.commit()

            else:

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

                # print ("\n")
                # print(conf_rm)
                # print ("\n")

                event_obj = Event(event_id=event_id,
                                  etag=etag,
                                  creator=creator,
                                  start=start,
                                  end=end,
                                  created_at=created_at,
                                  updated_at=updated_at,
                                  summary=summary)
                                  # conf_rm=conf_rm)

                db.session.add(event_obj)
                db.session.commit()

                calevent = CalEvent(calendar_id=id_,
                                    event_id=event_id,
                                    status=status)

                db.session.add(calevent)
                db.session.commit()

            # responseStatus = ResponseStatus(event_id=event_id)

# if __name__ == '__main__':
#     connect_to_db(app)
#     print ('connect to db')
#     main()
#     print('added to database')
