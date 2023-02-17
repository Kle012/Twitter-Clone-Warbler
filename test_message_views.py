"""Message View tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser", email="test@test.com", password="testuser", image_url=None)

        self.testuser_id = 12123
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_unauthorized_add(self):
        """Test for unauthorized (or logged-out) message adding."""
        with self.client as client:
            res = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
    
    def test_invalid_user_add(self):
        """Test for adding message by an invalid user (not existed)"""
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 1000000 
                # user does not exist
            res = client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
    
    def test_message(self):
        """Test for showing a message."""
        m = Message(
            id=12345,
            text='Testing for message',
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
            m = Message.query.get(12345)
            res = client.get(f'/messages/{m.id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(m.text, str(res.data))
    
    def test_message_delete(self):
        """Test for delete a message."""
        m = Message(
            id=12345,
            text='Testing for message',
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id
            
            res = client.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            m = Message.query.get(12345)
            self.assertIsNone(m)
    
    def test_unauthorized_delete(self):
        """Test for unauthorized delete."""
        u = User.signup(username='unauthorized', email='unauthorized@test.com', password='unauthorized', image_url=None)
        u.id = 65654

        m = Message(
            id=12345,
            text='Testing for message',
            user_id = self.testuser_id
        )

        db.session.add_all([u,m])
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = 65654
            
            res = client.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))

            m = Message.query.get(12345)
            self.assertIsNotNone(m)
        
    def test_unauthorized_delete(self):
        """Test for logged-out delete."""
        m = Message(
            id=12345,
            text='Testing for message',
            user_id = self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as client:
            res = client.post('/messages/12345/delete', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
    
            m = Message.query.get(12345)
            self.assertIsNotNone(m)