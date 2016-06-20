import os
import unittest
from server import app
import server
from model import connect_to_db, db, test_data


class LoggedOut(unittest.TestCase):
    """Flask tests with logged out user."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_homepage(self):
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('collaboration', result.data)
        print "Homepage 200"

    def test_session(self):
        with self.client.session_transaction() as sess:
            self.assertNotIn('sub', sess)
        print "Tested session"


class Loggedin(unittest.TestCase):
    """Flask tests with logged in user."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'key'
        self.client = app.test_client()

        with self.client.session_transaction() as sess:
            sess["sub"] = os.environ['SUB']

        # Mocks calendar list
        def _mock_calendar_options():
            return ['meggie.engineering@gmail.com']

        server.get_calendar_options = _mock_calendar_options

    def tearDown(self):
        with self.client.session_transaction() as sess:
            sess.pop("sub", None)

    def test_dashboard(self):
        result = self.client.get('/dashboard')
        self.assertEqual(result.status_code, 200)
        self.assertIn('logout', result.data)
        print "Tested dashboard"


class HelperFunctions(unittest.TestCase):
    """Flask tests for helper functions."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_get_matrix(self):
        self.assertEqual(server.get_matrix({u'name1': {'id': 1, 'name': u'name1'},
                                            u'name2': {'id': 0, 'name': u'name2'}}),
                                            [[0, 0], [0, 0]])
        print "Tested get matrix"

    def test_to_datetime(self):
        self.assertEqual(server.to_datetime('05/30/2016'), server.datetime(2016, 5, 30, 0, 0))
        print "Tested to datetime"


class DoughnutDb(unittest.TestCase):
    """Doughnut chart tests that use the database."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        # Connect to test database
        connect_to_db(app, "postgresql:///cals_test")
        print "Built test db"

        # Create tables and seed sample data
        db.create_all()
        test_data()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def test_get_event_type(self):
        selected_calendar = "meggie.engineering@gmail.com"
        startdate = server.datetime(2016, 7, 14, 0, 0)
        enddate = server.datetime(2016, 7, 16, 0, 0)
        events = server.get_event_type(selected_calendar,
                                       startdate,
                                       enddate)
        self.assertEqual(events[0].event_id, "abc")
        self.assertEqual(events[1].event_id, "defg")
        print "Tested get event type"

    def test_total_durations(self):
        selected_calendar = "reuben.engineering@gmail.com"
        startdate = server.datetime(2016, 7, 14, 0, 0)
        enddate = server.datetime(2016, 7, 16, 0, 0)
        events = server.get_event_type(selected_calendar,
                                       startdate,
                                       enddate)
        result = {u'one-on-one': 60, u'vertical': 120}
        self.assertEqual(server.total_durations(events), result)
        print "Tested total durations"

    def test_doughnut_data(self):
        selected_calendar = "jessie.engineering@gmail.com"
        startdate = server.datetime(2016, 7, 14, 0, 0)
        enddate = server.datetime(2016, 7, 16, 0, 0)
        events = server.get_event_type(selected_calendar,
                                       startdate,
                                       enddate)
        labels_and_durations = server.total_durations(events)
        result = {'durations': [120, 120], 'labels': [u'one-on-one', u'vertical']}
        self.assertEqual(server.doughnut_data(labels_and_durations), result)


class ChordDb(unittest.TestCase):
    """Chord diagram tests that use the database."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        # Connect to test database
        connect_to_db(app, "postgresql:///cals_test")
        print "Built test db"

        # Create tables and seed sample data
        db.create_all()
        test_data()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def test_get_team_events(self):
        selected_calendars = ["meggie.engineering@gmail.com",
                              "jessie.engineering@gmail.com"]
        startdate = "07/14/2016"
        enddate = "07/16/2016"
        result = {'event_id': u'hij',
                  'duration': 120,
                  'calendars': [u'Jessie', u'Reuben'],
                  'summary': u'standup'}
        self.assertIn(result, server.get_team_events(selected_calendars,
                                                     startdate,
                                                     enddate))
        print "Tested get team events"

    def test_populate_matrix(self):
        selected_calendars = ["meggie.engineering@gmail.com",
                              "jessie.engineering@gmail.com",
                              "reuben.engineering@gmail.com"]
        startdate = "07/14/2016"
        enddate = "07/16/2016"
        events = server.get_team_events(selected_calendars, startdate, enddate)
        mpr = server.get_mapper(selected_calendars)
        matrix = server.get_matrix(mpr)
        self.assertEqual(server.populate_matrix(events, mpr, matrix),
                         [[0, 120, 60], [120, 0, 120], [60, 120, 0]])
        print "Tested populate matrix"


if __name__ == "__main__":
    unittest.main()
