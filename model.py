from flask_sqlalchemy import SQLAlchemy

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


class User(db.Model):
    """Logged-in user"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):

        return "<User user_id={}>".format(self.user_id)


class Calendar(db.Model):
    """Calendars that are shared with user"""

    __tablename__ = "calendars"

    calendar_id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    summary = db.Column(db.String(100), nullable=True)
    etag = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(1000), nullable=True)
    timezone = db.Column(db.String(100), nullable=False)
    selected = db.Column(db.String(10), nullable=True)
    primary = db.Column(db.String(10), nullable=True)

    def __repr__(self):

        return "<Calendar calendar_id={}>".format(self.calendar_id,
                                                  self.user_id)


class GuestResponse(db.Model):

    __tablename__ = "guest_responses"

    guest_response_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    calendar_id = db.Column(db.String(100), db.ForeignKey('calendars.calendar_id'))
    event_id = db.Column(db.String(100), db.ForeignKey('events.event_id'))
    status = db.Column(db.String(20), nullable=True)
    # cancelled


class Event(db.Model):
    """Each event on each calendar."""

    __tablename__ = "events"

    event_id = db.Column(db.String(100), primary_key=True)
    etag = db.Column(db.String(100), nullable=True)
    creator = db.Column(db.String(100), nullable=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.String(1000), nullable=True)

    #Define relationship to movie
    # movie = db.relationship("Movie", backref=db.backref("ratings", order_by=rating_id))

    def __repr__(self):

        return "<Event event_id={}, calendar_id={}>".format(self.event_id,
                                                            self.calendar_id)


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///calanalytics'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    from server import app
    import os

    os.system("dropdb calanalytics")
    os.system("createdb calanalytics")

    connect_to_db(app)
    print "Connected to DB."

    # makes tables and columns
    db.create_all()

    user = User(user_id=1)

    db.session.add(user)
    db.session.commit()
