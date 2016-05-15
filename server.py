import os
from flask import Flask, render_template, redirect, url_for, jsonify  # session, flash, request
# from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import quickstart
# import httplib2
# from apiclient import discovery, errors
# from oauth2client import client
from model import connect_to_db, Event  # db
import datetime

app = Flask(__name__)
app.secret_key = os.environ["FLASK_APP_KEY"]
app.jinja_env.undefined = StrictUndefined

# import pdb; pdb.set_trace()


def next_week():

    now = datetime.datetime.utcnow()
    next_week = now + datetime.timedelta(weeks=1)
    wfh_next_week = Event.query.filter(Event.start < next_week,
                                       Event.summary.like('%WFH%')).all()

    return wfh_next_week


@app.route('/')
def index():
    """Google calendar login"""

    return render_template("homepage.html")


@app.route('/login/')
def login():
    """Login page"""

    quickstart.main()

    return redirect(url_for('upcoming'))


@app.route('/upcoming')
def upcoming():
    """Upcoming events data analysis"""

    wfh_next_week = next_week()

    return render_template("upcoming.html",
                           wfh_next_week=wfh_next_week)


@app.route('/weekly.json')
def weekly_data():

    wfh_next_week = next_week()
    week = {}

    for event in wfh_next_week:
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
                "label": "Out of Office",
                "fillColor": "rgba(151,187,205,0.2)",
                "strokeColor": "rgba(151,187,205,1)",
                "pointColor": "rgba(151,187,205,1)",
                "pointStrokeColor": "#fff",
                "pointHighlightFill": "#fff",
                "pointHighlightStroke": "rgba(151,187,205,1)",
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
