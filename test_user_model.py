"""User model tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        # User.query.delete()
        # Message.query.delete()
        # Follows.query.delete()

        db.drop_all()
        db.create_all()

        u1 = User.signup('test1', 'test1@yahoo.com', 'password', None)
        u1d = 11111
        u1.id = u1d

        u2 = User.signup('test2', 'test2@yahoo.com', 'password', None)
        u2d = 22222
        u2.id = u2d

        db.session.commit()

        u1 = User.query.get(u1d)
        u2 = User.query.get(u2d)

        self.u1 = u1
        self.u1d = u1d
        
        self.u2 = u2
        self.u2d = u2d

        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    
    
    # Follow tests

    def test_user_follows(self):
        """
        Test for following and followers relationship.
        """
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        """
        Does is_following work?
        """

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))
    
    def test_is_followed(self):
        """
        Does is_followed work?
        """

        self.u1.followers.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_followed_by(self.u2))
        self.assertFalse(self.u2.is_followed_by(self.u1))
    

    # User signup tests

    def test_valid_signup(self):
        """
        Does User.signup work with valid inputs?
        """
        u_test = User.signup('testvalid', 'valid@test.com', 'password', None)
        uid = 99999
        u_test.id = uid

        db.session.commit()

        u_test = User.query.get(uid)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, 'testvalid')
        self.assertEqual(u_test.email, 'valid@test.com')
        self.assertNotEqual(u_test.password, 'password')

        # bcrypt strings start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))
    
    def test_not_valid_email(self):
        """
        Does User.signup fail with invalid email?
        """
        not_valid = User.signup('not_valid', None, 'password', None)
        notid = 12345
        not_valid.id = notid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_not_valid_password(self):
        """
        Does User.signup fail with invalid password?
        """
        with self.assertRaises(ValueError) as context:
            User.signup("invalid_pass", "invalid@invalid.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("invalid_pass", "invalid@invalid.com", None, None)


    # User authenticate tests
    
    def test_authenticate(self):
        """
        Does User.authenticate work with valid inouts?
        """
        u = User.authenticate(self.u1.username, 'password')
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1d)
    
    def test_invalid_username(self):
        """
        Does User.authenticate fail with invalid username?
        """
        self.assertFalse(User.authenticate('invalid_username', 'password'))
    
    def test_invalid_password(self):
        """
        Does User.authenticate fail with invalid password?
        """
        self.assertFalse(User.authenticate(self.u1.username, 'invalidpassword'))
