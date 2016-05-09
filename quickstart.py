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
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """

    #calls get credentials function
    credentials = get_credentials()

    http = credentials.authorize(httplib2.Http())

    service = discovery.build('calendar', 'v3', http=http)

    # 'Z' indicates UTC time
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    print('Getting the upcoming 10 events')

    # calendarResult = service.calendarList() #<googleapiclient.discovery.Resource object at 0x1032201d0>
    # calendarResult = service.calendarList().list() #<googleapiclient.http.HttpRequest object at 0x103120390>
    # calendarResult = service.calendarList().list().execute() # dictionary

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
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['start'].get('date'))

        # print variables and the value to the summary key
        print(start, end, event['summary'])


if __name__ == '__main__':
    main()
