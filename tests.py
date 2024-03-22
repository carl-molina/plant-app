from sqlalchemy.exc import IntegrityError
from models import db, Plant, User
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

TEST_USER_DATA_NEW = dict(
    username="newuser",
    email="new@user.com",
    first_name="new",
    last_name="user",
    bio="This is a new test user.",
    password="secretpassword2",
)

TEST_PLANT_DATA = dict(
    common_name="Rose",
    scientific_name="Rosa",
    cycle="Perennial",
    watering="Weekly",
    sunlight="Full Sun",
)


#######################################
# homepage


class HomepageViewsTestCase(TestCase):
    """Tests about homepage."""

    def test_homepage(self):
        """Tests homepage positive views."""
        with app.test_client() as client:
            resp = client.get("/")
            self.assertIn(b'Test: homepage.html loaded.', resp.data)
            self.assertIn(b'Plant App', resp.data)
            self.assertIn(b'An App to Document Your Plant Journey', resp.data)


#######################################
# saved plants page


class SavedViewsTestCase(TestCase):
    """Tests about Saved Plants page."""

    def setUp(self):
        """Before each test, add sample user."""

        User.query.delete()
        user = User.register(**TEST_USER_DATA)
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        """After each test, remove all users."""

        db.session.rollback()

        User.query.delete()
        db.session.commit()

    def test_saved_plants_page(self):
        """Tests for saved plants page on logged-in user."""
        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get("/saved", follow_redirects=True)
            self.assertIn(b'Test: saved.html loaded.', resp.data)
            self.assertIn(b'Saved Plants page coming soon!', resp.data)

    def test_saved_plants_page_not_logged_in(self):
        with app.test_client() as client:
            """Tests for saved plants page on not logged-in user."""
            resp = client.get("/saved", follow_redirects=True)
            self.assertIn(b"You&#39;re not logged in.", resp.data)
            self.assertIn(b"Welcome Back!", resp.data)
            self.assertIn(b"Username", resp.data)
            self.assertIn(b"Password", resp.data)
            self.assertIn(b"Log In", resp.data)
            self.assertIn(b"Cancel", resp.data)


#######################################
# features page


class FeaturesViewsTestCast(TestCase):
    """Tests about Features page."""

    def test_features_page(self):
        with app.test_client() as client:
            resp = client.get("/features")
            self.assertIn(b'Test: features.html loaded.', resp.data)


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


#######################################
# login/logout/registration

class AuthViewsTestCase(TestCase):
    """Tests for views on logging in/logging out/registration."""

    def setUp(self):
        """Before each test, add sample users."""

        User.query.delete()

        user = User.register(**TEST_USER_DATA)

        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """After each test, remove all users."""

        db.session.rollback()

        User.query.delete()
        db.session.commit()

    def test_signup(self):
        """Tests for successful user signup."""

        with app.test_client() as client:
            resp = client.get("/signup")
            self.assertIn(b'Test: sign-form.html loaded.', resp.data)
            self.assertIn(b'Sign Up', resp.data)
            self.assertIn(b'Username', resp.data)
            self.assertIn(b'First Name', resp.data)
            self.assertIn(b'Last Name', resp.data)
            self.assertIn(b'Bio', resp.data)
            self.assertIn(b'Email', resp.data)
            self.assertIn(b'Password', resp.data)
            self.assertIn(b'Image URL', resp.data)

            resp = client.post(
                "/signup",
                data=TEST_USER_DATA_NEW,
                follow_redirects=True,
            )

            self.assertIn(b"You are signed up and logged in.", resp.data)
            self.assertTrue(session.get(CURR_USER_KEY))

    def test_signup_username_taken(self):
        """Tests for invalid signup (username already taken)."""

        with app.test_client() as client:
            resp = client.get("/signup")
            self.assertIn(b"Sign Up", resp.data)

            resp = client.post(
                "/signup",
                data=TEST_USER_DATA,
                follow_redirects=True,
            )

            self.assertIn(b"Username already taken", resp.data)

    def test_login(self):
        """Tests for user login."""

        with app.test_client() as client:
            resp = client.get("/login")
            self.assertIn(b"Test: login-form.html loaded.", resp.data)
            self.assertIn(b"Welcome Back!", resp.data)

            resp = client.post(
                "/login",
                data={"username": "testname", "password": "secretpassword"},
                follow_redirects=True,
            )

            self.assertIn(b"Hello, testname!", resp.data)
            self.assertEqual(session.get(CURR_USER_KEY), self.user_id)

    def test_login_invalid_credentials(self):
        """Tests for invalid login credentials."""

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={"username": "testname", "password": "wrongpw"},
                follow_redirects=True,
            )

            self.assertIn(b"Invalid credentials", resp.data)

    def test_logout(self):
        """Tests for user logout."""

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.post("/logout", follow_redirects=True)

            self.assertIn(b"You have successfully logged out.", resp.data)
            self.assertEqual(session.get(CURR_USER_KEY), None)

    def test_profile(self):
        """Tests for user profile page."""

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get("/profile", follow_redirects=True)

            self.assertIn(b"Test: profile detail.html loaded.", resp.data)
            self.assertIn(b"test name", resp.data)
            self.assertIn(b"<p><b>Username:</b> testname</p>", resp.data)
            self.assertIn(b"Edit Your Profile", resp.data)
            self.assertIn(b"You have no liked plants.", resp.data)

#######################################
# navbar

class NavBarTestCase(TestCase):
    """Tests navigation bar."""

    def setUp(self):
        """Before tests, add sample user."""

        User.query.delete()

        user = User.register(**TEST_USER_DATA)

        db.session.commit()

        self.user_id = user.id

    def tearDown(self):
        """After tests, remove all users."""

        db.session.rollback()

        User.query.delete()
        db.session.commit()

    def test_anon_navbar(self):
        """Tests view of navbar when user not logged in."""

        with app.test_client() as client:
            resp = client.get('/')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Sign Up', resp.data)
            self.assertIn(b'Log In', resp.data)
            self.assertNotIn(b'Log Out', resp.data)

    def test_logged_in_navbar(self):
        """Tests view of navbar when user logged in."""

        with app.test_client() as client:
            login_for_test(client, self.user_id)
            resp = client.get('/')

            self.assertIn(b'Log Out', resp.data)
            self.assertIn(b'test name', resp.data)
            self.assertNotIn(b'Sign Up', resp.data)
            self.assertNotIn(b'Log In', resp.data)

#######################################
# plants/plant

# TODO: add view test for plant detail page here

class PlantDetailViewsTestCase(TestCase):
    """Tests for plant detail page."""

    def setUp(self):
        """Before each test, add sample plant."""

        Plant.query.delete()
        new_plant = Plant(**TEST_PLANT_DATA)
        db.session.add(new_plant)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


    def tearDown(self):
        """After each test, remove all plants."""

        db.session.rollback()

        Plant.query.delete()
        db.session.commit()

    def test_view_plant_detail(self):
        """Test viewing a specific plant detail page."""
        with app.test_client() as client:
            resp = client.get('/plants/1')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Rose', resp.data)
            self.assertIn(b'Cycle: Perennial', resp.data)