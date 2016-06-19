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
        print "Session empty when logged out"


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
        print "Dashboard 200"


class HelperFunctions(unittest.TestCase):
    """Flask tests for helper functions."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_get_matrix(self):
        self.assertEqual(server.get_matrix({u'name1': {'id': 1, 'name': u'name1'},
                                            u'name2': {'id': 0, 'name': u'name2'}}),
                                            [[0, 0], [0, 0]])
        print "Built empty matrix"

    def test_to_datetime(self):
        self.assertEqual(server.to_datetime('05/30/2016'), server.datetime(2016, 5, 30, 0, 0))
        print "Correct datetime input"


class Database(unittest.TestCase):
    """Flask tests that use the database."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        # Connect to test database
        connect_to_db(app, "postgresql:///cals_test")
        print "Built test db"

        # Create tables and add sample data
        db.create_all()
        test_data()

    def tearDown(self):
        db.session.close()
        db.drop_all()


if __name__ == "__main__":
    unittest.main()
