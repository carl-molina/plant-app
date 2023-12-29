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
from models import connect_db, db, User, Like
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


@app.get("/")
def homepage():
    """Show homepage."""

    form = PlantSearchForm()

    return render_template('homepage.html', form=form)


#######################################
# user signup/login/logout routes


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup.
    GET: shows registration form.
    POST: processes registration. If valid, adds user, logs them in, and
    redirects to cafe list. If invalid, re-presents form w/ invalid message.
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
    POST: processes login. If valid, logs user in and redirects to cafe list.
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
# cafes routes


@app.get('/cafes')
def cafe_list():
    """Return list of all cafes."""

    cafes = Cafe.query.order_by('name').all()

    return render_template(
        '/cafe/list.html',
        cafes=cafes,
    )


@app.get('/cafes/<int:cafe_id>')
def cafe_detail(cafe_id):
    """Show detail for cafe."""

    cafe = Cafe.query.get_or_404(cafe_id)

    return render_template(
        'cafe/detail.html',
        cafe=cafe,
    )


@app.route('/cafes/add', methods=["GET", "POST"])
# Quotations for each method was the ^ bug ^.
def add_new_cafe():
    """GET: show form for adding a cafe. Form accepts:
            name: required
            description: optional
            url: optional, else must be valid URL
            address: required
            city_code: must be drop-down menu of cities in db
            image_url: optional, else must be valid URL

    POST: handles adding new cafe.
    """

    if not g.user or not g.user.admin:
        flash("Only admins can add/edit cafes.")
        return redirect(url_for("cafe_list"))


    form = AddEditCafeForm()
    form.city_code.choices = get_cities()

    if form.validate_on_submit():
        # data = {k: v for k, v in form.data.items() if k != "csrf_token"}
        # new_cafe = Cafe(**data)
        # ^ old way, need to validate if image_url is empty string instead:
        new_cafe = Cafe(
            name=form.name.data,
            description=form.description.data,
            url=form.url.data,
            address=form.address.data,
            city_code=form.city_code.data,
            image_url=form.image_url.data or Cafe.image_url.default.arg,
        )

        db.session.add(new_cafe)

        try:
            db.session.commit()

        except IntegrityError:
            flash("Could not add cafe to database.")
            return render_template('/cafe/add-form.html', form=form)

        flash(f'{new_cafe.name} added.')
        new_cafe.save_map()
        return redirect(url_for('cafe_detail', cafe_id=new_cafe.id))

    else:
        return render_template('/cafe/add-form.html', form=form)


@app.route('/cafes/<int:cafe_id>/edit', methods=["GET", "POST"])
def edit_cafe(cafe_id):
    """GET: show form for editing cafe. Form fields same as adding new cafe.
    POST: handles editing cafe.
    """

    if not g.user or not g.user.admin:
        flash("Only admins can add/edit cafes.")
        return redirect(url_for("cafe_list"))

    cafe = Cafe.query.get_or_404(cafe_id)

    form = AddEditCafeForm(obj=cafe)
    form.city_code.choices = get_cities()

    if form.validate_on_submit():
        if not form.image_url.data:
            form.image_url.data = Cafe.image_url.default.arg

        form.populate_obj(cafe)

        try:
            db.session.commit()

        except IntegrityError:
            flash("Could not save changes.")
            return render_template('/cafe/edit-form.html', form=form, cafe=cafe)

        flash(f'{cafe.name} edited.')
        cafe.save_map()
        return redirect(url_for('cafe_detail', cafe_id=cafe_id))

    else:
        return render_template('/cafe/edit-form.html', form=form, cafe=cafe)


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

    plant_id = int(request.args.get('plant_id'))
    plant = Plant.query.get_or_404(plant_id)

    like = Like.query.filter(
        (Like.user_id==g.user.id) & (Like.plant_id==plant.id)
        ).one_or_none()

    if like:
        like = True
    else:
        like = False

    return jsonify({"likes": like})


# TODO: currently here


@app.post('/api/like')
def handle_user_like():
    """Handles user liking plant."""

    if not g.user:
        return jsonify({"error": "Not logged in"})


# TODO: maybe add plant to DB here? If already in db, raise IntegrityError and
# don't have to add it to DB.

    plant_id = int(request.json['plant_id'])
    plant = Plant.query.get_or_404(plant_id)

    g.user.liked_plants.append(plant)

    db.session.commit()

    return jsonify({"liked": plant_id})


@app.post('/api/unlike')
def handle_user_unliking():
    """Handles user unliking a cafe."""

    if not g.user:
        return jsonify({"error": "Not logged in"})

    plant_id = int(request.json['plant_id'])
    plant = Plant.query.get_or_404(plant_id)

    g.user.liked_cafes.remove(plant)

    db.session.commit()

    return jsonify({"unliked": plant_id})


#######################################
# plants routes


print('Before entering handle_json_form_data')
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
        # note to self: might need API route to be '-list?'


        print('This is resp', resp)
        # for example, if we use API key and search for 'monstera':
        # https://perenual.com/api/species-list?key=sk-wfpE6589044314e5d3581&q=monstera


        # TODO: left here for the night; work on implementing search feature
        # tomorrow!! Exciting.

        plant_data = resp.json()
        print('This is plant_data', plant_data)

        print('This is plant_data jsonify', jsonify(plant_data))
        return jsonify(plant_data)

    else:
        error = {key: val for key, val in form.errors.items()}
        return jsonify(error=error)