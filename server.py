from jinja2 import StrictUndefined

# import json
# import sys
import os

from flask import Flask, render_template, redirect, request, flash, session, url_for, jsonify
# from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db
import quickstart

import os
# import json
import httplib2
import datetime

from apiclient import discovery, errors
from oauth2client import client
from flask import Flask, session, render_template, request, flash, redirect, url_for
# from flask.ext.session import Session
# from flask.json import jsonify
from flask_debugtoolbar import DebugToolbarExtension
from model import db, connect_to_db, Event, Calendar, User, UserCal, CalEvent

app = Flask(__name__)

app.secret_key = os.environ["FLASK_APP_KEY"]

app.jinja_env.undefined = StrictUndefined

# Session(app)


# @app.route('/')
# def login():
#     """Google calendar login"""

#     return render_template("login.html")


# @app.route("/oauth2callback")
# def oauth2callback():
#     flow = client.flow_from_clientsecrets('client_secret.json',
#                                           scope='https://www.googleapis.com/auth/calendar.readonly',
#                                           redirect_uri=url_for('oauth2callback', _external=True))
#     if 'code' not in request.args:
#         auth_uri = flow.step1_get_authorize_url()
#         return redirect(auth_uri)
#         print "code not in request.args"
#     else:
#         auth_code = request.args.get('code')
#         credentials = flow.step2_exchange(auth_code)
#         session['credentials'] = credentials.to_json()
#         return redirect(url_for('login'))
#         print "got to auth_code"


# @app.route('/calendar')
# def calendar():
#     print("got to credentials")
#     # import pdb; pdb.set_trace()
#     if 'credentials' not in session:
#         return redirect(url_for('oauth2callback'))
#     credentials = client.OAuth2Credentials.from_json(session['credentials'])
#     print("got to access token")
#     if credentials.access_token_expired:
#         return redirect(url_for('oauth2callback'))
#     else:
#         http_auth = credentials.authorize(httplib2.Http())
#         service = discovery.build('calendar', 'v3', http_auth)
#     print "built service"
#     return service

#     # import pdb; pdb.set_trace()


@app.route('/')
def index():
    """Google calendar login"""

    return render_template("homepage.html")


@app.route('/login/')
def login():
    """Login page"""

    # print "Hi, Taylor!"
    quickstart.main()

    return redirect(url_for('upcoming'))


@app.route('/upcoming')
def upcoming():
    """Upcoming events data analysis"""

    current_time = datetime.datetime.utcnow()
    one_week_from_now = current_time + datetime.timedelta(weeks=1)

    # event = Event.query.filter(Event.start < ten_weeks_from_now).all()
    week_from_now = Event.query.filter(Event.start < one_week_from_now).all()
    next_week_wfh = Event.query.filter(Event.start < one_week_from_now,
                                       Event.summary.like('%WFH%')).all()

    return render_template("upcoming.html",
                           next_week_wfh=next_week_wfh)


@app.route('/weekly.json')
def weekly_data():

    current_time = datetime.datetime.utcnow()
    one_week_from_now = current_time + datetime.timedelta(weeks=1)

    next_week_wfh = Event.query.filter(Event.start < one_week_from_now, Event.summary.like('%WFH%')).all()

    week = {}

    for event in next_week_wfh:
        day = event.start.weekday()
        for calevent in event.calevents:
            week.setdefault(day, []).append(calevent.calendar_id)

    week_data = [0, 0, 0, 0, 0, 0, 0]

    for key, value in week.iteritems():
        week_data[key] = len(value)

    data_dict = {
        "labels": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "datasets": [
            {
                "label": "In Office",
                "fillColor": "rgba(220,220,220,0.2)",
                "strokeColor": "rgba(220,220,220,1)",
                "pointColor": "rgba(220,220,220,1)",
                "pointStrokeColor": "#fff",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(220,220,220,1)",
                "data": week_data
            }
        ]
    }
    return jsonify(data_dict)


if __name__ == "__main__":
    app.debug = True

    connect_to_db(app)

    # DebugToolbarExtension(app)

    app.run()
