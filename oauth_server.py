import os
from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask.json import jsonify
from jinja2 import StrictUndefined
import httplib2
from apiclient import discovery, errors
from oauth2client import client
from model import connect_to_db, Event, Calendar, User, UserCal, CalEvent
from datetime import datetime, timedelta
import logging
from seed import seed_db

app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined

# import pdb; pdb.set_trace()


def next_week():
    """Pulls events for next week from db"""

    # datetime with timezone
    now = datetime.now()

    # need to only pull events from calendars associated with user_id
    next_week = now + timedelta(weeks=1)

    wfh_next_week = Event.query.filter(Event.start < next_week,
                                       Event.summary.like('%WFH%')).all()

    return wfh_next_week


def out_for_lunch():
    """Out for lunch next week"""

    now = datetime.now()
    lunch_start = datetime.time(12)
    lunch_end = datetime.time(13)

    next_week = now + timedelta(weeks=1)

    ofl_next_week = Event.query.filter(Event.start < next_week,
                                       Event.start_time < lunch_start,
                                       Event.end_time > lunch_end,
                                       (Event.summary.like('%site%') | Event.summary.like('%ooo%'))).all()

    return ofl_next_week


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
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('calendar'))


# def batched_events(request_id, response, exception):
#         if exception is not None:
#             print "batched events error"
#         else:
#             print("\n")
#             print request_id, response
#             print("\n")


@app.route('/calendar')
def calendar():

    print("got to credentials")
    print datetime.now()
    print("\n")

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        people_service = discovery.build('people', 'v1', http_auth)
        calendar_service = discovery.build('calendar', 'v3', http_auth)
        event_service = discovery.build('calendar', 'v3', http_auth)

    print "built services"
    print datetime.now()
    print("\n")

    print("before profile api call")
    print datetime.now()
    print("\n")

    profile = people_service.people().get(resourceName='people/me').execute()
    user_id = profile['names'][0]['metadata']['source']['id']

    print("after profile api call")
    print datetime.now()
    print("\n")

    # user_exists = User.query.get(user_id)

    # if user_exists:
    #     # get sync token
    #     user_sync_token = user_exists.user_sync_token
    #     calendarsResult = calendar_service.calendarList().list(syncToken=user_sync_token).execute()
    #     # update calendar info

    # else:

    print("before calendar api call")
    print datetime.now()
    print("\n")

    calendarsResult = calendar_service.calendarList().list(
        fields='nextSyncToken, etag, items, items/etag, items/id, \
        items/primary, items/selected, items/timeZone, items/summary').execute()

    print("calendarsResult")
    print calendarsResult
    print("\n")

    print("after calendar api call")
    print datetime.now()
    print("\n")

    calendars = calendarsResult.get('items', [])

    # now = datetime.utcnow().isoformat() + 'Z'
    # three_months = datetime.now() + timedelta(weeks=12)
    # three_months = three_months.isoformat() + 'Z'

    eventsResult = {}

    def batched_events(request_id, response, exception):
        if exception is not None:
            print exception
        else:
            eventsResult[request_id] = response

    batch = event_service.new_batch_http_request(callback=batched_events)

    id_list = [calendar['id'] for calendar in calendars]

    print("before events api call")
    print datetime.now()
    print("\n")

    for id_ in id_list:

        print("before calendar db queries")
        print datetime.now()
        print("\n")
        calendar_exists = Calendar.query.get(user_id)
        if calendar_exists:
            batch.add(calendar_service.events().list(calendarId=id_,
                                                     syncToken=calendar_exists.calendar_sync_token,
                                                     singleEvents=True),
                                                     request_id=id_)
        else:
            batch.add(calendar_service.events().list(calendarId=id_,
                                                     singleEvents=True),
                                                     request_id=id_)
    print("after calendar db queries")
    print datetime.now()
    print("\n")

    batch.execute()

    print("after events api call")
    print datetime.now()
    print("\n")

    print("before db seed")
    print datetime.now()
    print("\n")

    print "eventsResult"
    print eventsResult
    print("\n")
    seed_db(profile, user_id, calendarsResult, eventsResult)
    print("after db seed")
    print datetime.now()
    print("\n")

    # db query
    wfh_next_week = next_week()
    print("after db query")
    print datetime.now()
    print("\n")

    return render_template('upcoming.html',
                           wfh_next_week=wfh_next_week)


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


@app.route('/breakdown')
def breakdown():

    wfh_next_week = next_week()

    return render_template('breakdown.html',
                           wfh_next_week=wfh_next_week)


# @app.route('/history')
# def index():
#     """Historical events data analysis"""

#     return render_template("history.html")


# @app.route("/setting")
# def settings_page():
#     """Settings page."""

#     return render_template("settings.html")


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
