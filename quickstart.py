from __future__ import print_function
import httplib2
import os

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


# def oauth():
#        """Your application must be authenticated, the user must
#     grant access for your application, and the user must be authenticated
#     in order to grant that access.
#     """


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
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """

    # calls get_credentials function
    credentials = get_credentials()

    # Creates an httplib2.Http object to handle HTTP requests and authorizes it
    http = credentials.authorize(httplib2.Http())

    # The apiclient.discovery.build() function returns an instance of an API service
    # object can be used to make API calls. The object is constructed with
    # methods specific to the calendar API. The arguments provided are:
    #   name of the API ('calendar')
    #   version of the API you are using ('v3')
    #   authorized httplib2.Http() object that can be used for API calls

    service = discovery.build('calendar', 'v3', http=http)

    # 'Z' indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    print('Getting the upcoming 10 events')

    # calendarResult = service.calendarList()
    """Collection object: <googleapiclient.discovery.Resource object at 0x1032201d0>"""

    # calendarResult = service.calendarList().list()
    """Http request object: <googleapiclient.http.HttpRequest object at 0x103120390>"""

    # calendarResult = service.calendarList().list().execute()
    """Creating a request does not actually call the API. To execute the request
    and get a response, call the execute() function. The response is a Python
    object built from the JSON response sent by the API server."""

    # eventsResult is a dictionary
    eventsResult = service.events().list(

        # filter on the dictionary
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()

    # list of event dictionaries, value for 'items' key
    events = eventsResult.get('items', [])

    # if empty list, print no upcoming events
    if not events:
        print('No upcoming events found.')

    # for each event dictionary in the events list
    for event in events:

        # start key has a dictionary as the value
        # if the key dateTime exists bind that to start
        # if dateTime does not exist, bind the date
        calendar_email = event['summary']
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['start'].get('date'))
        creator = event['creator'].get('email', [])
        kind = event['kind']
        status = event['status']
        summary = event['summary']
        event_id = event['id']
        created_dateTime = event['created']
        updated_dateTime = event['updated']

        # print variables and the value to the summary key
        print ("******")
        print ("Calendar for: ", calendar_email)
        print ("Event Title: ", summary)
        print ("Event id:", event_id)
        print ("Created: ", created_dateTime)
        print ("Updated ", updated_dateTime)
        print ("Start DateTime: ", start)
        print ("End DateTime: ", end)
        print ("Event Creator: ", creator)
        print ("Kind: ", kind)
        print ("Status: ", status)

        if 'attendees' in event:
            attendees = event['attendees']

            for attendee in attendees:
                if 'resource' in attendee:
                    display_name = attendee['displayName']
                    print ("Where: ", display_name)

                #TODO: remove primary email from guest
                else:
                    guest = attendee['email']
                    print ("Who: ", guest)


if __name__ == '__main__':
    main()
