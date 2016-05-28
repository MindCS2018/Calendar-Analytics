import os
from flask import Flask, session, render_template, request
from flask import flash, redirect, url_for, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, flow_from_clientsecrets, OAuth2Credentials
from model import connect_to_db, Event, Calendar, User, UserCal, CalEvent, db
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

    profile_result = profile_api_call(people_service)
    calendars_result = calendar_api_call(calendar_service)
    events_result = event_api_call(event_service,
                                   calendar_service,
                                   calendars_result)

    # database seed
    seed_db(profile_result, calendars_result, events_result)

    return redirect("/dashboard")


def pull_credentials():
    """Pulls credentials out of session"""

    return OAuth2Credentials.from_json(session['credentials'])


def create_user_id():
    """Adds google id_token to session"""

    cred_dict = json.loads(session['credentials'])
    user_id = cred_dict['id_token']['sub']
    session['sub'] = user_id


def get_service_objects(http_auth):
    """Builds google API service objects"""

    people_service = build('people', 'v1', http_auth)
    calendar_service = build('calendar', 'v3', http_auth)
    event_service = build('calendar', 'v3', http_auth)

    return people_service, calendar_service, event_service


def get_dates():
    """Datetime variables for events API call"""

    now = datetime.utcnow().isoformat() + 'Z'
    three_months = datetime.now() + timedelta(weeks=12)
    three_months = three_months.isoformat() + 'Z'

    return now, three_months


def calendar_api_call(calendar_service):
    """Executes google calendar api call"""

    return calendar_service.calendarList().list(
           fields='etag, items, items/etag, items/id, items/primary, \
           items/selected, items/timeZone, items/summary').execute()


def profile_api_call(people_service):
    """Executes google people api call"""

    return people_service.people().get(resourceName='people/me').execute()


def event_api_call(event_service, calendar_service, calendars_result):
    """Executes one batched google calendar api call,
    returns event information for each shared calendar"""

    events_result = {}

    def batched_events(request_id, response, exception):  # events batch callback
        if exception is not None:
            print "batching error"
        else:
            events_result[request_id] = response

    batch = event_service.new_batch_http_request(callback=batched_events)

    now, three_months = get_dates()

    calendars = calendars_result.get('items', [])  # list of calendar objects
    id_list = [calendar['id'] for calendar in calendars]

    for calendar_id in id_list:  # API request for events in each calendar

        batch.add(event_service.events().list(calendarId=calendar_id,
                                              timeMin=now,
                                              timeMax=three_months,
                                              maxResults=100,
                                              singleEvents=True,
                                              orderBy='startTime'),
                  request_id=calendar_id)

    batch.execute()  # executes batch api call

    return events_result


def get_user_id():
    """Returns user_id"""

    return session['sub']


def seed_db(profile_result, calendars_result, events_result):

    user_id = get_user_id()

    seed_user(profile_result, user_id)
    seed_calendars(calendars_result, user_id)
    seed_events(events_result)


def get_calendar_options():

    user_id = get_user_id()

    calendars = UserCal.query.filter_by(user_id=user_id).all()

    calendar_options = []
    for cal in calendars:
        calendar_options.append(cal.calendar.summary)

    return calendar_options


@app.route('/chord_diagram.json')
def chord_diagram():

    # receive from ajax request
    selected_calendars = request.args.getlist('calendar')

    mpr = get_mapper(selected_calendars)
    events = get_events(selected_calendars)
    matrix = get_matrix(mpr)
    emptyMatrix = get_matrix(mpr)  # to test if final matrix is empty

    meetingsMatrix = populate_matrix(events, mpr, matrix)

    data = {"mpr": mpr, "meetingsMatrix": meetingsMatrix, "emptyMatrix": emptyMatrix}

    return jsonify(data)


@app.route('/dashboard')
def dashboard():
    """"""

    calendar_options = get_calendar_options()

    return render_template('dashboard.html',
                           calendar_options=calendar_options)


def get_mapper(selected_calendars):
    """Recives list of selected calendars for visualization,
       returns mapper object."""

    mpr = {}
    x = 0

    for calendar in selected_calendars:
        calendar_summary = (calendar.split("@")[0]).title()
        mpr[calendar_summary] = {"id": x,
                                 "name": calendar_summary}
        x += 1

    return mpr


@app.route("/receive_dates")
def receive_dates():

    startdate = request.args.get("startdate")
    print startdate
    return "hello"


def get_events(selected_calendars):
    """"""

    events = set()

    for cal in selected_calendars:
        for calevent in CalEvent.query.filter_by(calendar_id=cal).all():
            events.add(calevent.event)

    # cals = CalEvent.query.options(db.joinedload('event')).all()

    # print cals

    evts = db.session.query(CalEvent, Event).join(Event).all()

    for calevent, event in evts:
        if calevent.calendar_id == "megan@lunchdragon.com" and event.start > datetime(2016, 5, 27):
            print event

    events = list(events)

    return [event.serialize() for event in events]


def get_matrix(mpr):
    """Calculates number of nodes from mapper object,
       returns matrix of all zeros."""

    nodes = len(mpr.keys())

    return [[0] * nodes for i in range(nodes)]


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
