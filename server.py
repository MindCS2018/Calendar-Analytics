import os
from flask import Flask, session, render_template, request
from flask import flash, redirect, url_for, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, flow_from_clientsecrets, OAuth2Credentials
from model import connect_to_db, Event, Calendar, User, UserCal, CalEvent
from datetime import datetime, timedelta
import logging
from seed import seed_user, seed_calendars, seed_events
import json
import itertools


app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined


# import pdb; pdb.set_trace()


@app.route('/')
def login():
    """Renders login page"""

    return render_template("login.html")


@app.route("/oauth2callback")
def oauth2callback():
    """Authenticates google user and authorizes app"""

    logging.basicConfig(filename='debug.log', level=logging.WARNING)

    flow = flow_from_clientsecrets(
                  'client_secret.json',
                  scope='https://www.googleapis.com/auth/calendar.readonly \
                  https://www.googleapis.com/auth/plus.login',
                  redirect_uri=url_for('oauth2callback', _external=True))

    flow.params['access_type'] = 'online'
    flow.params['approval_prompt'] = 'auto'

    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)  # creates credentials object
        session['credentials'] = credentials.to_json()
        return redirect(url_for('oauth2'))


def get_service_objects(http_auth):
    """Builds google API service objects"""

    people_service = build('people', 'v1', http_auth)
    calendar_service = build('calendar', 'v3', http_auth)
    event_service = build('calendar', 'v3', http_auth)

    return people_service, calendar_service, event_service


def pull_credentials():
    """Pulls credentials out of session"""

    return OAuth2Credentials.from_json(session['credentials'])


def create_user_id():
    """Adds google id_token to session"""

    cred_dict = json.loads(session['credentials'])
    user_id = cred_dict['id_token']['sub']
    session['sub'] = user_id


def get_user_id():
    """Returns user_id"""

    return session['sub']


@app.route('/oauth2')
def oauth2():

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = pull_credentials()

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        people_service, calendar_service, event_service = get_service_objects(http_auth)

    create_user_id()

    # profile api call
    profile = people_service.people().get(resourceName='people/me').execute()

    # calendars api call
    calendarsResult = calendar_service.calendarList().list(
        fields='etag, items, items/etag, items/id, items/primary, \
        items/selected, items/timeZone, items/summary').execute()

    # empty dictionary for events api call
    eventsResult = {}

    # callback from events batch needs to be created before batch request
    def batched_events(request_id, response, exception):
        if exception is not None:
            print "batching error"
        else:
            eventsResult[request_id] = response

    # batch request
    batch = event_service.new_batch_http_request(callback=batched_events)

    # datetime variables for event API calls
    now = datetime.utcnow().isoformat() + 'Z'
    three_months = datetime.now() + timedelta(weeks=12)
    three_months = three_months.isoformat() + 'Z'

    # list of calendar dictionaries
    calendars = calendarsResult.get('items', [])

    # creates list of calendar_ids to iterate through
    id_list = [calendar['id'] for calendar in calendars]

    # API request for events in each calendar
    for calendar_id in id_list:

        batch.add(calendar_service.events().list(calendarId=calendar_id,
                                                 timeMin=now,
                                                 timeMax=three_months,
                                                 maxResults=100,
                                                 singleEvents=True,
                                                 orderBy='startTime'),
                  request_id=calendar_id)

    # executes batch api call
    batch.execute()

    # database seed
    seed_db(profile, calendarsResult, eventsResult)

    return redirect("/calendars")


def seed_db(profile, calendarsResult, eventsResult):

    user_id = get_user_id()

    seed_user(profile, user_id)
    seed_calendars(calendarsResult, user_id)
    seed_events(eventsResult)


@app.route("/calendars")
def calendars():
    """"""

    user_id = get_user_id()

    calendars = UserCal.query.filter_by(user_id=user_id).all()

    calendar_options = []
    for cal in calendars:
        calendar_options.append(cal.calendar.summary)

    return render_template('calendars.html',
                           calendar_options=calendar_options)


def get_mapper(selected):
    """Recives list of selected calendars for visualization,
       returns mapper object."""

    mpr = {}
    x = 0

    for calendar in selected:
        calendar_summary = (calendar.split("@")[0]).title()
        mpr[calendar_summary] = {"id": x,
                                 "name": calendar_summary}
        x += 1

    return mpr


def get_matrix(mpr):
    """Calculates number of nodes from mapper object,
       returns matrix of all zeros."""

    nodes = len(mpr.keys())

    matrix = [[0] * nodes for i in range(nodes)]

    return matrix


def get_events(selected):
    """"""

    events = set()
    # boom = set()

    # can i query for event date here?

    for cal in selected:
        for calevent in CalEvent.query.filter_by(calendar_id=cal).all():
            events.add(calevent.event)
            # boom.add(calevent.event.start)

    events = list(events)
    # boom = list(boom)
    # print("boom**")
    # print boom
    events = [event.serialize() for event in events]

    return events


def populate_matrix(events, mpr, matrix):
    """"""

    for event in events:
        attendees = event['calendars']
        for item in itertools.combinations(attendees, 2):
            if item[0] in mpr and item[1] in mpr:
                item = list(item)
                item[0] = mpr[item[0]]['id']
                item[1] = mpr[item[1]]['id']
                item.append(event['duration'])
                matrix[item[0]][item[1]] += item[2]
                matrix[item[1]][item[0]] += item[2]

    return matrix


@app.route('/dashboard', methods=['POST'])
def dashboard():
    """"""

    # list of selected calendars
    selected = request.form.getlist('calendar')

    # builds matrix
    mpr = get_mapper(selected)
    events = get_events(selected)
    matrix = get_matrix(mpr)
    emptyMatrix = get_matrix(mpr)  # to test if final matrix is empty

    meetingsMatrix = populate_matrix(events, mpr, matrix)

    mpr = json.dumps(mpr)
    meetingsMatrix = {"data": meetingsMatrix}
    meetingsMatrix = json.dumps(meetingsMatrix)

    return render_template('dashboard.html',
                           mpr=mpr,
                           meetingsMatrix=meetingsMatrix)


@app.route('/logout')
def logout():
    """On logout, revokes oauth credentials,
       and deletes them from the session"""

    credentials = pull_credentials()

    credentials.revoke(httplib2.Http())

    del session['credentials']

    return render_template("logout.html")


if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    # DebugToolbarExtension(app)

    app.run()
