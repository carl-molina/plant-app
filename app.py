"""Flask app for Plant App."""

import os
from dotenv import load_dotenv

load_dotenv()

from flask import (
    Flask, render_template, session, flash, redirect, url_for, g, jsonify,
    request
)

import requests

from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Like, Plant
from forms import (
    CSRFProtection, PlantSearchForm, SignupForm, LoginForm
)

from sqlalchemy.exc import IntegrityError
# from utils import

API_KEY = os.environ['PERENUAL_API_KEY']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECERT_KEY', 'sssshhhh')
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['WTF_CSRF_ENABLED'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)

#######################################
# 404 error route


@app.errorhandler(404)
def not_found(e):
    """Custom 404 page when user visits an incorrect URL."""

    return render_template('404.html')


#######################################
# auth & auth routes


CURR_USER_KEY = "curr_user"
NOT_LOGGED_IN_MSG = "You're not logged in."


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user instance to Flask global using
    user.id.
    """

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_only_form():
    """Add a CSRF-only form so that every route can use it."""

    g.csrf_form = CSRFProtection()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


#######################################
# homepage


@app.get('/')
def homepage():
    """Show homepage."""

    form = PlantSearchForm()

    return render_template('homepage.html', form=form)


#######################################
# about

@app.get('/about')
def about():
    """Show about page."""

    return render_template('about.html')


#######################################
# features

@app.get('/features')
def features():
    """Show features page."""

    return render_template('features.html')


#######################################
# user signup/login/logout routes


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup.
    GET: shows registration form.
    POST: processes registration. If valid, adds user, logs them in, and
    redirects to homepage. If invalid, re-presents form w/ invalid message.
    """

    do_logout()

    form = SignupForm()

    if form.validate_on_submit():
        new_user = User.register(
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            bio=form.bio.data,
            email=form.email.data,
            password=form.password.data,
            image_url=form.image_url.data or User.image_url.default.arg,
        )
        try:
            db.session.commit()

        except IntegrityError:
            flash('Username already taken.', 'danger')
            return render_template('/auth/signup-form.html', form=form)

        do_login(new_user)
        flash('You are signed up and logged in.')
        return redirect(url_for('homepage'))

    else:
        return render_template('/auth/signup-form.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles logging in user.
    GET: shows login form.
    POST: processes login. If valid, logs user in and redirects to homepage.
    If invalid, re-presents form w/ invalid message.
    """

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f'Hello, {user.username}!')
            return redirect(url_for('homepage'))

        flash('Invalid credentials.', 'danger')

    return render_template('/auth/login-form.html', form=form)


@app.post('/logout')
def logout():
    """Handles logging out user."""

    if not g.csrf_form.validate_on_submit() or not g.user:
        flash("Access unauthorized", "danger")
        return redirect(url_for('homepage'))

    do_logout()

    flash('You have successfully logged out.')
    return redirect(url_for('homepage'))


#######################################
# general user routes


@app.get('/profile')
def show_profile():
    """Shows user profile."""

    if not g.user:
        # if not logged in, you shouldn't be able to view a user's profile
        flash(NOT_LOGGED_IN_MSG, 'danger')
        return redirect(url_for('login'))

    return render_template('/profile/detail.html', user=g.user)


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit current user profile.
    GET: show profile edit form.
    POST: process profile edit. Redirects to profile page.
    """

    if not g.user:
        flash(NOT_LOGGED_IN_MSG, 'danger')
        return redirect(url_for('login'))

    form = ProfileEditForm(obj=g.user)

    if form.validate_on_submit():
        if not form.image_url.data:
            form.image_url.data = User.image_url.default.arg

        form.populate_obj(g.user)

        try:
            db.session.commit()

        except IntegrityError:
            flash("Update failed.")
            return render_template('/profile/edit-form.html', form=form)

        flash("Profile edited.")
        return redirect(url_for('show_profile'))

    return render_template('/profile/edit-form.html', form=form)


#######################################
# plant/plants routes


@app.get('/plants/<int:plant_id>')
def plant_detail(plant_id):
    """Show detail for plant."""

    plant = Plant.query.get_or_404(plant_id)

    return render_template(
        'plant/detail.html',
        plant=plant,
        show_edit=g.user and g.user.admin,
    )


# @app.route('/plants/<int:plant_id>/edit', methods=["GET", "POST"])
# def edit_plant(plant_id):
#     """GET: show form for editing plant. Form fields same as adding new plant.
#     POST: handles editing plant.
#     """

#     if not g.user or not g.user.admin:
#         flash("Only admins can add/edit plants.")
#         return redirect(url_for("homepage"))

#     plant = Plant.query.get_or_404(plant_id)

#     form = AddEditPlantForm(obj=plant)

#     if form.validate_on_submit():
#         if not form.default_image.data:
#             form.default_image.data = Plant.image_url.default.arg

#         form.populate_obj(plant)

#         try:
#             db.session.commit()

#         except IntegrityError:
#             flash("Could not save changes.")
#             return render_template('/plant/edit-form.html', form=form, plant=plant)

#         flash(f'{plant.common_name} edited.')
#         return redirect(url_for('plant_detail', plant_id=plant_id))

#     else:
#         return render_template('/plant/edit-form.html', form=form, plant=plant)


#######################################
# likes routes


@app.get('/api/likes')
def likes_plant():
    """Given plant_id in the URL query string, checks if the current user likes
    specific plant. Returns JSON:

    {"likes": true|false}

    """

    if not g.user:
        return jsonify({"error": "Not logged in"})

    # ^ actually, bookmark icon empty should still exist even if user is not
    # logged in. When a non-user clicks on empty bookmark, it should redirect
    # them to login to use that feature. Once logged in, bring them back to
    # original location.

    print('We got into likes_plant on backend/server-side!')
    print('This is plant_id', int(request.args.get('plant_id')))
    plant_id = int(request.args.get('plant_id'))
    print('This is plant_id', plant_id)

    plant = Plant.query.get_or_404(plant_id)

    like = Like.query.filter(
        (Like.user_id==g.user.id) & (Like.plant_id==plant.id)
        ).one_or_none()

    if like:
        like = True
    else:
        like = False

    return jsonify({"likes": like})


@app.post('/api/like')
def handle_user_like():
    """Handles user liking plant."""

    if not g.user:
        return jsonify({"error": "Not logged in"})

    plant_id = int(request.json['plant_id'])
    plant = Plant.query.get_or_404(plant_id)

    g.user.liked_plants.append(plant)

    db.session.commit()

    return jsonify({"liked": plant_id})


@app.post('/api/unlike')
def handle_user_unliking():
    """Handles user unliking a plant."""

    if not g.user:
        return jsonify({"error": "Not logged in"})

    plant_id = int(request.json['plant_id'])
    plant = Plant.query.get_or_404(plant_id)

    g.user.liked_plants.remove(plant)

    db.session.commit()

    return jsonify({"unliked": plant_id})


#######################################
# Perenual API routes
# TODO: add plant detail route for Perenual API request


@app.post('/api/get-plant-list')
def handle_json_form_data():
    """Takes in a JSON body with the following:

        searchTerm: input value from user searching for plant

    Interprets JSON data, sends requests to Perenual API, and returns JSON resp.
    """

    print('We got into handle_json_form_data!')

    data = request.json
    print('This is data', data)

    print('We got passed form validation! Now checking JSON.')
    form = PlantSearchForm(obj=data)

    print('This is form', form)

    if form.validate_on_submit():
        print('We got passed form validation for PlantSearchForm!')
        term = form.term.data

        print('This is term', term)

        resp = requests.get(
            f'https://perenual.com/api/species-list',
            params={
                "key": API_KEY,
                "q": term,
                "order": "asc",
            }
        )

        print('This is resp', resp)
        # for example, if we use API key and search for 'monstera':
        # https://perenual.com/api/species-list?key=sk-wfpE6589044314e5d3581&q=monstera

        plant_data = resp.json()
        print('This is plant_data', plant_data)

        for plant in plant_data.get("data"):

            print('This is plant', plant)

            default_img = None
            if plant.get('default_image', None) == None:
                default_img = Plant.default_image.default.arg

            elif 'medium_url' not in plant.get('default_image') and 'original_url' in plant.get('default_image'):
                default_img = plant['default_image']['original_url']

            new_plant = Plant(
                id = plant.get('id'),
                common_name = plant.get('common_name'),
                scientific_name = plant.get('scientific_name'),
                cycle = plant.get('cycle'),
                watering = plant.get('watering'),
                sunlight = plant.get('sunlight'),
                default_image = (default_img or
                                 plant['default_image']['medium_url'])
            )

            db.session.add(new_plant)

            try:
                db.session.commit()
                # flash(f'{new_plant.common_name} added w/ id {new_plant.id}')

            except IntegrityError:
                # flash(f'Could not add plant id {new_plant.id} to db. ' +
                #       f'Possibly already added {new_plant.common_name}.')
                db.session.rollback()

            # flash(f'{new_plant.common_name} added w/ id {new_plant.id}')

        print('This is plant_data jsonify', jsonify(plant_data))
        return jsonify(plant_data)

    else:
        error = {key: val for key, val in form.errors.items()}
        return jsonify(error=error)
