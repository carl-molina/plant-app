"Tests for Plant App."

import os

os.environ["DATABASE_URL"] = "postgresql:///plant_app_test"

from unittest import TestCase

from flask import session
from app import app, CURR_USER_KEY
from models import db, Plant, User, Like
