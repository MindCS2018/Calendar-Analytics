from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User of app"""

    __tablename__ = "users"

    user_id = db.Column(db.String(10000), primary_key=True)
    first_name = db.Column(db.String(200), nullable=True)
    last_name = db.Column(db.String(200), nullable=True)
    full_name = db.Column(db.String(200), nullable=True)
    # user_sync_token = db.Column(db.String(200), nullable=True)


class UserCal(db.Model):
    """Each calendar shared with a user"""

    __tablename__ = "usercals"

    usercal_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.String(10000), db.ForeignKey('users.user_id'))
    calendar_id = db.Column(db.String(100), db.ForeignKey('calendars.calendar_id'))
    primary = db.Column(db.String(10), nullable=True)
    selected = db.Column(db.String(10), nullable=True)

    user = db.relationship("User", backref=db.backref("usercals", order_by=usercal_id))

    calendar = db.relationship("Calendar", backref=db.backref("usercals", order_by=usercal_id))


class Calendar(db.Model):
    """Each calendar"""

    __tablename__ = "calendars"

    calendar_id = db.Column(db.String(100), primary_key=True)
    etag = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=False)
    # calendar_sync_token = db.Column(db.String(200), nullable=True)


class CalEvent(db.Model):
    """Relationship between events and calendars"""

    __tablename__ = "calevents"

    calevent_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    calendar_id = db.Column(db.String(100), db.ForeignKey('calendars.calendar_id'))
    event_id = db.Column(db.String(10000), db.ForeignKey('events.event_id'))
    # status = db.Column(db.String(20), nullable=True)

    event = db.relationship("Event", backref=db.backref("calevents", order_by=calevent_id))

    calendar = db.relationship("Calendar", backref=db.backref("calevents", order_by=calevent_id))


class Event(db.Model):
    """Each event"""

    __tablename__ = "events"

    event_id = db.Column(db.String(10000), primary_key=True)
    etag = db.Column(db.String(100), nullable=True)
    creator = db.Column(db.String(100), nullable=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    duration = db.Column(db.Interval, nullable=True)
    # updated_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.String(1000), nullable=True)
    # conf_rm = db.Column(db.String(40), nullable=True)


def connect_to_db(app):
    """Connects database to Flask app."""

    # configures PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///cals'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    from server import app
    import os

    os.system("dropdb cals")
    os.system("createdb cals")

    connect_to_db(app)
    print "Connected to DB."

    # creates tables and columns
    db.create_all()
