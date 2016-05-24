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


app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined

# import pdb; pdb.set_trace()


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
        return redirect(url_for('oauth'))


@app.route('/oauth')
def oauth():

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        # creates api service objects
        http_auth = credentials.authorize(httplib2.Http())
        people_service = build('people', 'v1', http_auth)
        calendar_service = build('calendar', 'v3', http_auth)
        event_service = build('calendar', 'v3', http_auth)

    # profile api call
    profile = people_service.people().get(resourceName='people/me').execute()

    cred_dict = json.loads(session['credentials'])
    user_id = cred_dict['id_token']['sub']

    session["user_id"] = user_id

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

    credentials.revoke(httplib2.Http())  # for demo purposes

    return redirect("/calendars")


@app.route("/calendars")
def calendars():

    user_id = session['user_id']

    all_calendars = UserCal.query.filter_by(user_id=user_id).all()

    calendar_options = []
    for calendar in all_calendars:
        calendar_options.append(calendar.calendar.summary)

    return render_template('calendars.html',
                           calendar_options=calendar_options)


@app.route('/dashboard', methods=['POST'])
def dashboard():

    # choice of calendars
    selected = request.form.getlist('calendar')

    # creates mapper object
    mpr = {}
    x = 0
    for calendar in selected:
        calendar_summary = (calendar.split("@")[0]).title()
        mpr[calendar_summary] = {"id": x,
                                 "name": calendar_summary}
        x += 1

    # creates event object
    event_objs = set()

    for cal in selected:
        for calevent in CalEvent.query.filter_by(calendar_id=cal).all():
            event_objs.add(calevent.event)

    event_objs = list(event_objs)
    chord_data = {"data": [event_obj.serialize() for event_obj in event_objs]}

    mpr = json.dumps(mpr)
    chord_data = json.dumps(chord_data)

    return render_template('dashboard.html',
                           mpr=mpr,
                           chord_data=chord_data)


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
