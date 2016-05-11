from jinja2 import StrictUndefined

# import json
# import sys
# import os

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

app.secret_key = "will-fill-in-later"

app.jinja_env.undefined = StrictUndefined

# CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']

# app.secret_key = "Tobefilledin"

#Use os.envir (see lecture notes on how to store)


# @app.route('/')
# def index():
#     """Index page"""

#     return render_template("login.html")


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


# @app.route('/signout')
# def index():
#     """Signout"""

#     return redirect("/")


if __name__ == "__main__":
    app.debug = True

    connect_to_db(app)

    DebugToolbarExtension(app)

    app.run()
