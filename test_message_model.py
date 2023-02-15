import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test view for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.uid = 98765
        u = User.signup('message_test', 'messages@test.com', 'password', None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)
        self.client = app.test_client()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_message_model(self):
        """Does the basic model work?"""
        
        m = Message(
            text='Hello',
            user_id = self.uid
        )

        db.session.add(m)
        db.session.commit()

        #User should have 1 message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, 'Hello')
    
    def test_message_likes(self):
        """ Does toggle like work?
        """
        m1 = Message(
            text='Test_Like1',
            user_id = self.uid
        )

        m2 = Message(
            text='Test_Like2',
            user_id = self.uid
        )

        u = User.signup('testmsg', 'msg@test.com', 'password', None)
        uid = 55555
        u.id = uid
        db.session.add(m1)
        db.session.add(m2)
        db.session.add(u)
        db.session.commit()

        u.likes.append(m1)
        db.session.commit()

        like = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, m1.id)

