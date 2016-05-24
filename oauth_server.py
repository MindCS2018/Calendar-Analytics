import os
from flask import Flask, session, render_template, request
from flask import flash, redirect, url_for, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import httplib2
from apiclient.discovery import build
from oauth2client import client
from model import connect_to_db, Event, Calendar, User, UserCal, CalEvent
from datetime import datetime, timedelta
import logging
from seed import seed_user, seed_calendars, seed_events
import json
import numpy


app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined

# import pdb; pdb.set_trace()


def events_query():

    return Event.query.all()


def next_week():
    """Pulls events for next week from db"""

    # datetime with timezone
    now = datetime.now()

    # need to only pull events from calendars associated with user_id
    next_week = now + timedelta(weeks=1)

    return Event.query.filter(Event.start < next_week,
                              Event.summary.like('%WFH%')).all()


# def out_for_lunch():
#     """Out for lunch next week"""

#     now = datetime.now()
#     lunch_start = datetime.time(12)
#     lunch_end = datetime.time(13)

#     next_week = now + timedelta(weeks=1)

#     ofl_next_week = Event.query.filter(Event.start < next_week,
#                                        Event.start_time < lunch_start,
#                                        Event.end_time > lunch_end,
#                                        (Event.summary.like('%site%') | Event.summary.like('%ooo%'))).all()

#     return ofl_next_week


@app.route('/')
def login():
    """Google calendar login"""

    return render_template("login.html")


@app.route("/oauth2callback")
def oauth2callback():

    logging.basicConfig(filename='debug.log', level=logging.WARNING)

    flow = client.flow_from_clientsecrets('client_secret.json',
                                          scope='https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/plus.login',
                                          redirect_uri=url_for('oauth2callback', _external=True))

    flow.params['access_type'] = 'online'
    flow.params['approval_prompt'] = 'auto'

    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('calendar'))


@app.route('/calendar')
def calendar():

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        # creates api service objects
        # print session['credentials']
        http_auth = credentials.authorize(httplib2.Http())
        people_service = build('people', 'v1', http_auth)
        calendar_service = build('calendar', 'v3', http_auth)
        event_service = build('calendar', 'v3', http_auth)

    # profile api call
    profile = people_service.people().get(resourceName='people/me').execute()
    # user_id = profile['names'][0]['metadata']['source']['id']
    cred_dict = json.loads(session['credentials'])
    user_id = cred_dict['id_token']['sub']

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
    seed_user(profile, user_id)
    seed_calendars(calendarsResult, user_id)
    seed_events(eventsResult)

    calendar_options = []
    for calendar_obj in calendarsResult['items']:
        calendar_options.append(calendar_obj['summary'])

    # credentials.revoke(httplib2.Http())  # for demo purposes

    return render_template('calendars.html',
                           calendar_options=calendar_options)


@app.route('/mapper.json')
def build_mapper():

    # selected = request.form.getlist('calendar')
    print("**selected**")
    # print selected
    print("****")

    # list of calendar objects
    # TODO: pull from choose calendars page
    calendar_objs = Calendar.query.all()

    # creates mapper object
    mpr = {}
    x = 0
    for calendar in calendar_objs:
        calendar_summary = (calendar.calendar_id.split("@")[0]).title()
        mpr[calendar_summary] = {"id": x,
                                 "name": calendar_summary}
        x += 1
    print("**mpr**")
    print mpr
    print("****")

#     print mpr

#     ids = set()

#     for event in events:
#         for calevent in event.calevents:
#             ids.add(calevent.calendar_id)

#     n = str(len(ids))

#     empty_matrix = numpy.zeros(shape=(n, n))

    return jsonify(mpr)


# @app.route('/matrix.json')
# def build_matrix():

#     n = 8

#     empty_matrix = numpy.zeros(shape=(n, n))

#     matrix_data = {"data": {"date": empty_matrix}}

#     return jsonify(matrix_data)


@app.route('/events.json')
def build_events():

    events = events_query()

    chord_data = {"data": [event.serialize() for event in events]}

    return jsonify(chord_data)


@app.route('/dashboard', methods=['POST'])
def d3():

    # creating json here

    selected = request.form.getlist('calendar')
    print("**selected**")
    print selected
    print("****")

    # list of calendar objects
    # TODO: pull from choose calendars page
    # calendar_objs = Calendar.query.all()

    # creates mapper object
    mpr = {}
    x = 0
    for calendar in selected:
        calendar_summary = (calendar.split("@")[0]).title()
        mpr[calendar_summary] = {"id": x,
                                 "name": calendar_summary}
        x += 1

    mpr = json.dumps(mpr)

    return render_template('meetings.html',
                           mpr=mpr)


@app.route('/weekly.json')
def weekly_data():
    """Creates data for weekly chart"""

    wfh_next_week = next_week()

    week = {}

    for event in wfh_next_week:
        day = event.start.weekday()
        for calevent in event.calevents:
            week.setdefault(day, set()).add(calevent.calendar_id)

    data = [0, 0, 0, 0, 0, 0, 0]

    for key, value in week.iteritems():
        data[key] = len(value)

    data_dict = {
        "labels": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "datasets": [
            {
                "label": "Out of Office",
                "fillColor": "rgba(151,187,205,0.2)",
                "strokeColor": "rgba(151,187,205,1)",
                "pointColor": "rgba(151,187,205,1)",
                "pointStrokeColor": "#fff",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(151,187,205,1)",
                "data": data
            },
            {
                "label": "Out for Lunch",
                "fillColor": "rgba(219,186,52,0.4)",
                "strokeColor": "rgba(220,220,220,1)",
                "pointColor": "rgba(220,220,220,1)",
                "pointStrokeColor": "#fff",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(151,187,205,1)",
                "data": [0, 1, 1, 1, 3, 0, 0]
            },
        ]
    }
    return jsonify(data_dict)


@app.route('/chart')
def chart():

    # db query
    wfh_next_week = next_week()

    return render_template('chart.html',
                           wfh_next_week=wfh_next_week)


@app.route('/breakdown')
def breakdown():

    wfh_next_week = next_week()

    return render_template('breakdown.html',
                           wfh_next_week=wfh_next_week)


@app.route('/logout')
def logout():
    """Logout"""

    del session['credentials']

    return render_template("logout.html")


if __name__ == "__main__":

    app.debug = True

    connect_to_db(app)

    # DebugToolbarExtension(app)

    app.run()
