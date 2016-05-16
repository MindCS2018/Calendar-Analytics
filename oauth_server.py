from jinja2 import StrictUndefined

# # import json
# # import sys
# import os

# from flask import Flask, render_template, redirect, request, flash, session, url_for
# from flask_debugtoolbar import DebugToolbarExtension
# from model import connect_to_db, db
# import quickstart

import os
# import json
import httplib2

from apiclient import discovery, errors
from oauth2client import client
from flask import Flask, session, render_template, request, flash, redirect, url_for
# from flask.ext.session import Session
from flask.json import jsonify
from flask_debugtoolbar import DebugToolbarExtension
from model import db, connect_to_db, Event, Calendar, User, UserCal, CalEvent
import logging

app = Flask(__name__)

app.secret_key = os.environ["FLASK_APP_KEY"]

app.jinja_env.undefined = StrictUndefined

# Session(app)


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


@app.route('/calendar')
def calendar():
    print("got to credentials")

    # import pdb; pdb.set_trace()
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(session['credentials'])

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http_auth)
    print "built service"
    # return service
    return render_template('calendar.html')

    # import pdb; pdb.set_trace()


# @app.route('/')
# def index():
#     """Google calendar login"""

#     return render_template("homepage.html")


# @app.route('/login/')
# def login():
#     """Login page"""

#     # print "Hi, Taylor!"
#     quickstart.main()

#     return redirect(url_for('index'))


# @app.route('/upcoming')
# def index():
#     """Upcoming events data analysis"""

#     return render_template("upcoming.html")


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

    # connect_to_db(app)

    # DebugToolbarExtension(app)

    app.run()
