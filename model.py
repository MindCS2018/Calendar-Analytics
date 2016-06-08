from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User of app"""

    __tablename__ = "users"

    user_id = db.Column(db.String(10000), primary_key=True)
    first_name = db.Column(db.String(200), nullable=True)
    last_name = db.Column(db.String(200), nullable=True)


class UserCal(db.Model):
    """Each calendar shared with a user"""

    __tablename__ = "usercals"

    usercal_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.String(10000), db.ForeignKey('users.user_id'))
    calendar_id = db.Column(db.String(100), db.ForeignKey('calendars.calendar_id'))
    primary = db.Column(db.String(10), nullable=False)
    selected = db.Column(db.String(10), nullable=False)

    user = db.relationship("User", backref=db.backref("usercals", order_by=usercal_id))

    calendar = db.relationship("Calendar", backref=db.backref("usercals", order_by=usercal_id))


class Calendar(db.Model):
    """Each calendar"""

    __tablename__ = "calendars"

    calendar_id = db.Column(db.String(100), primary_key=True)
    etag = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=False)


class CalEvent(db.Model):
    """Relationship between events and calendars"""

    __tablename__ = "calevents"

    calevent_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    calendar_id = db.Column(db.String(100), db.ForeignKey('calendars.calendar_id'))
    event_id = db.Column(db.String(10000), db.ForeignKey('events.event_id'))

    event = db.relationship("Event", backref=db.backref("calevents", order_by=calevent_id))

    calendar = db.relationship("Calendar", backref=db.backref("calevents", order_by=calevent_id))


class Event(db.Model):
    """Each event"""

    __tablename__ = "events"

    event_id = db.Column(db.String(10000), primary_key=True)
    etag = db.Column(db.String(100), nullable=False)
    creator = db.Column(db.String(100), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    summary = db.Column(db.String(1000), nullable=True)
    label = db.Column(db.String(100), nullable=True)

    @property
    def duration_minutes(self):
        """Given an event object,
        returns number of minutes."""

        time_delta = self.end - self.start
        minutes = int(time_delta.total_seconds()/60)
        return minutes

    def get_calendars(self):
        """Given an event object,
        return a list of calendar_ids associated with the event"""

        calendars = []
        for calevent in self.calevents:
            calendar = calevent.calendar_id.split(".")[0].title()
            calendars.append(calendar)

        return calendars

    def serialize(self):
        """Given a list of events,
        returns DB object as a dictionary"""

        calendars = self.get_calendars()

        return {"event_id": self.event_id,
                "duration": self.duration_minutes,
                "summary": self.summary,
                "calendars": calendars}


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
