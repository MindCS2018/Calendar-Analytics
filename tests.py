import os
import unittest
from server import app
import server
from model import connect_to_db, db


class LoggedOut(unittest.TestCase):

    def setUp(self):
        """Before each test."""

        self.client = app.test_client()
        app.config['TESTING'] = True

    def tearDown(self):
        """After each test."""

        pass

    def test_homepage(self):

        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('collaboration', result.data)


class Loggedin(unittest.TestCase):

    def setUp(self):
        """Before each test"""

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'key'
        self.client = app.test_client()

        # with self.client as test_client:
        with self.client.session_transaction() as sess:
            sess["sub"] = os.environ['SUB']

        # Make mocks
        def _mock_calendar_options():
            return ['meggie.engineering@gmail.com']

        server.get_calendar_options = _mock_calendar_options

    def tearDown(self):
        """After each test"""

        self.client = app.test_client()

        with self.client.session_transaction() as sess:
            del sess['sub']

    def test_dashboard(self):

        result = self.client.get('/dashboard')

        self.assertEqual(result.status_code, 200)
        self.assertIn('logout', result.data)


class HelperFunctions(unittest.TestCase):

    def setUp(self):
        """Before each test"""

        self.client = app.test_client()
        app.config['TESTING'] = True

    def tearDown(self):
        """After each test."""

    def test_get_matrix(self):
        self.assertEqual(server.get_matrix({u'name1': {'id': 1, 'name': u'name1'},
                                            u'name2': {'id': 0, 'name': u'name2'}}),
                                            [[0, 0], [0, 0]])

    def to_datetime(self):
        self.assertEqual(server.to_datetime('05/30/2016'),
                         server.datetime.datetime(2016, 5, 30, 0, 0))


# class HelperFunctionsDb(unittest.TestCase):

#     def setUp(self):
#         """Before each test"""

#         self.client = app.test_client()
#         app.config['TESTING'] = True

#     def tearDown(self):
#         """After each test."""


# class cahoots_tests_database(unittest.TestCase):
#     """Flask tests that use the database."""

#     def setUp(self):
#         """Stuff to do before every test."""

#         self.client = app.test_client()
#         app.config['TESTING'] = True

#         # Connect to test database
#         # Use name of test database here to override default database in model.py
#         connect_to_db(app, "postgresql:///testdb")

#         # Create tables and add sample data
#         db.create_all()
#         example_data()

#     def tearDown(self):
#         """Do at end of every test."""

#         db.session.close()
#         db.drop_all()

#     def test_pages(self):
#         #FIXME: test that the pages displays from all example_()_data() functions

#         pass

if __name__ == "__main__":
    unittest.main()
