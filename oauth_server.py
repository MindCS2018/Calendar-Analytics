import os
from flask import Flask, session, render_template, request, flash, redirect, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask.json import jsonify
from jinja2 import StrictUndefined
import httplib2
from apiclient import discovery, errors
from oauth2client import client
from model import connect_to_db, Event, Calendar, User, UserCal, CalEvent
import datetime
import logging
from seed import seed_db

app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined

# import pdb; pdb.set_trace()


def next_week():
    """Pulls events for next week from db"""

    now = datetime.datetime.utcnow()
    # need to only pull events from calendars associated with user_id
    next_week = now + datetime.timedelta(weeks=1)
    wfh_next_week = Event.query.filter(Event.start < next_week,
                                       Event.summary.like('%WFH%')).all()

    return wfh_next_week


@app.route('/')
def login():
    """Google calendar login"""

    return render_template("login.html")


@app.route("/oauth2callback")
def oauth2callback():

    logging.basicConfig(filename='debug.log', level=logging.WARNING)

    flow = client.flow_from_clientsecrets('client_secret.json',
                                          scope='https://www.googleapis.com/auth/calendar.readonly',
                                          redirect_uri=url_for('oauth2callback', _external=True))
    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        session['credentials'] = credentials.to_json()
        return redirect(url_for('calendar'))


# @app.route('/tokensignin', methods=['POST'])
# def tokensignin():

#     user_id = request.form.get("user_id")
#     username = request.form.get("username")
#     user_email = request.form.get("user_email")

#     return "hello"


@app.route('/calendar', methods=['GET', 'POST'])
def calendar():

    print("got to credentials")
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http_auth)
    print "built service"

    # user_id = session['user_id']
    # username = session['username']
    # user_email = session['user_email']

    # seed database
    seed_db(service)
    # seed(service, user_id, username, user_email)

    # db query
    wfh_next_week = next_week()

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
            }
        ]
    }
    return jsonify(data_dict)


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
