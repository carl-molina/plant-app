from sqlalchemy.exc import IntegrityError
from models import db, Plant, User, Like
from app import app, CURR_USER_KEY
from flask import session
from unittest import TestCase
"Tests for Plant App."

import os

os.environ["DATABASE_URL"] = "postgresql:///plant_app_test"


# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()


#######################################
# helper functions for tests


def debug_html(response, label="DEBUGGING"):  # pragma: no cover
    """Prints HTML response; useful for debugging tests."""

    print("\n\n\n", "*********", label, "\n")
    print(response.data.decode('utf8'))
    print("\n\n")


def login_for_test(client, user_id):
    """Log in this user."""

    with client.session_transaction() as sess:
        sess[CURR_USER_KEY] = user_id


#######################################
# data to use for test objects


TEST_USER_DATA = dict(
    username="testname",
    email="test@name.com",
    first_name="test",
    last_name="name",
    bio="This is test user.",
    password="secretpassword",
)


#######################################
# homepage


class HomepageViewsTestCase(TestCase):
    """Tests about homepage."""

    def test_homepage(self):
        with app.test_client() as client:
            resp = client.get("/")
            self.assertIn(b'Plant App', resp.data)
            self.assertIn(b'An App to Document Your Plant Journey', resp.data)


#######################################
# users

class UserModelTestCase(TestCase):
    """Tests for User Model."""

    def setUp(self):
        """Before each test, add sample user."""

        User.query.delete()
        user = User.register(**TEST_USER_DATA)
        db.session.commit()
        self.user = user

    def tearDown(self):
        """After each test, remove all users."""

        db.session.rollback()

        User.query.delete()
        db.session.commit()


    def test_authenticate(self):
        res = User.authenticate("testname", "secretpassword")
        self.assertEqual(res, self.user)


    def test_authenticate_fail(self):
        res = User.authenticate("no-such-user", "secret")
        self.assertFalse(res)

        res = User.authenticate("testname", "invalidpassword")
        self.assertFalse(res)


    def test_full_name(self):
        self.assertEqual(self.user.full_name, "test name")


    def test_register(self):
        u = User.register(**TEST_USER_DATA)
        # test that password gets bcrypt-hashed (all start w/$2b$)
        self.assertEqual(u.hashed_password[:4], "$2b$")
        db.session.rollback()
