"""User view tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, connect_db,User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()



