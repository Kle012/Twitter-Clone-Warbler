"""User view tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, connect_db,User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username='testuser', email='user@test.com', password='password0', image_url=None)
        self.testuser_id = 88888
        self.testuser.id = self.testuser_id

        self.u1 = User.signup(username='testuser1', email='user1@test.com', password='password1', image_url=None)
        self.u1_id = 77777
        self.u1.id = self.u1_id

        self.u2 = User.signup(username='testuser2', email='user2@test.com', password='password2', image_url=None)
        self.u2_id = 15973
        self.u2.id = self.u2_id

        self.u3 = User.signup(username='tuser3', email='user3@test.com', password='password3', image_url=None)

        self.u4 = User.signup(username='tuser4', email='user4@test.com', password='password4', image_url=None)
        
        db.session.commit()
    
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_index_page(self):
        """Test for users list."""
        with app.test_client() as client:
            res = client.get('/users')
            self.assertIn('testuser', str(res.data))
            self.assertIn('testuser1', str(res.data))
            self.assertIn('testuser2', str(res.data))
            self.assertIn('tuser3', str(res.data))
            self.assertIn('tuser4', str(res.data))
    
    def test_user_search(self):
        """Test for search function."""
        with app.test_client() as client:
            res = client.get('/users?q=test')
            self.assertIn('testuser', str(res.data))
            self.assertIn('testuser1', str(res.data))
            self.assertIn('testuser2', str(res.data))
            self.assertNotIn('tuser3', str(res.data))
            self.assertNotIn('tuser4', str(res.data))
    
    def test_user_show(self):
        """Test for a user detail."""
        with app.test_client() as client:
            res = client.get(f'/users/{self.testuser_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn('testuser', str(res.data))
    
    def setup_likes(self):
        """Create test message, add sample data."""
        m1 = Message(text='Hello Testing', user_id=self.testuser_id)
        m2 = Message(text='Warbles', user_id=self.u1_id)
        m3 = Message(id=24680, text='Twitter copycat', user_id=self.u2_id)

        db.session.add_all([m1,m2,m3])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id=24680)

        db.session.add(like)
        db.session.commit()
    
    def test_add_like(self):
        """Test for like function."""
        m = Message(id=13579, text='Add like test', user_id=self.u2_id)
        db.session.add(m)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.u1_id
            
            res = client.post('/messages/13579/like', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==13579).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.u1_id)
    
    def test_remove_like(self):
        """Test for remove like function."""
        self.setup_likes()

        m = Message.query.filter(Message.text=='Twitter copycat').one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.u1_id)

        # Make sure that testuser likes the message 'Twitter copycat'
        l = Likes.query.filter(Likes.user_id==self.testuser_id and Likes.message_id==m.id).one()
        self.assertIsNotNone(l)

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id
        
        # Toggle like
        res = client.post(f'/messages/{m.id}/like', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        likes = Likes.query.filter(Likes.message_id==m.id).all()
        # Like has been removed
        self.assertEqual(len(likes), 0)
    
    def test_unauthenticated_like(self):
        """Test for like function when user logged-out"""
        self.setup_likes()

        m = Message.query.filter(Message.text=='Twitter copycat').one()
        self.assertIsNotNone(m)

        count = Likes.query.count()

        with self.client as client:
            res = client.post(f'/messages/{m.id}/like', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))

            # Due to invalid request, the count of likes stay the same
            self.assertEqual(count, Likes.query.count())
    
    def setup_follows(self):
        """Create test follows, add sample data."""
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()
    
    # def test_following(self):
        """Test for following function."""
