import datetime
from django.db.models import Count
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate, APITestCase
from mist.serializers import CommentSerializer, PostSerializer, ProfileSerializer, UserSerializer
from mist.views import CommentView, PostView, ProfileView, UserCreate
from .models import Profile, Post, Comment

# Create your tests here.
class AuthTest(TestCase):
    def test_register_user(self):
        # insert user to database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous1@usc.edu',
                'username':'anonymous1', 
                'password':'anonymous1',
            },
            format='json',
        )
        raw_view = UserCreate.as_view()(response)
        # insertion should be successful
        self.assertEquals(raw_view.status_code, 201)

    def test_obtain_token_valid_user(self):
        # insert user into database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous2@usc.edu',
                'username':'anonymous2', 
                'password':'anonymous2',
            },
            format='json',
        )
        UserCreate.as_view()(response)
        # generate auth token
        response = factory.post('api-auth-token/',
            {
                'email':'anonymous2@usc.edu',
                'username':'anonymous2', 
                'password':'anonymous2'
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        # generation should be successful
        self.assertEquals(raw_view.status_code, 200)

class ProfileTest(TestCase):
    def setUp(self):
        # set up auth
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user)
        # initialize profiles
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan'
        )
        self.adam = Profile.objects.create(
            username='adamnovak',
            first_name='adam',
            last_name='novak'
        )
        # upload to database
        self.factory = APIRequestFactory()
        request = self.factory.post('/api/profiles', 
            ProfileSerializer(self.barath).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        request = self.factory.post('/api/profiles', 
            ProfileSerializer(self.adam).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        return
        
    def test_get_valid_profile(self):
        # get valid profile object
        profile = Profile.objects.get(username=self.barath.username)
        seralized_profile = ProfileSerializer(profile).data
        # get valid query object
        request = self.factory.get(
            '/api/profiles',
            {'username':self.barath.username},
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = ProfileView.as_view({'get':'list'})(request)
        data_view = raw_view.data[0]
        # should be identical
        self.assertEqual(seralized_profile, data_view)
        return
    
    def test_get_invalid_profile(self):
        # get invalid query object
        request = self.factory.get(
            '/api/profiles',
            {'username':'nonexistent'},
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = ProfileView.as_view({'get':'list'})(request)
        data_view = raw_view.data
        # should be empty
        self.assertEqual([], raw_view.data)
        return

class PostTest(TestCase):
    def setUp(self):
        # set up auth
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user)
        # initialize profiles + posts
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
        )
        self.post1 = Post.objects.create(
            title='faketitle1',
            text='faketext1',
            date=datetime.date(2020, 3, 5),
            author=self.barath,
        )
        self.post1.votes.add(self.barath)
        self.post2 = Post.objects.create(
            title='faketitle2',
            text='faketext2',
            date=datetime.date(2020, 3, 5),
            author=self.barath,
        )
        # upload to database
        self.factory = APIRequestFactory()
        request = self.factory.post('/api/profiles', 
            ProfileSerializer(self.barath).data, 
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        request = self.factory.post('/api/posts', 
            PostSerializer(self.post1).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        request = self.factory.post('/api/posts', 
            PostSerializer(self.post2).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        return

    def test_get_posts(self):
        # order all seralized posts by vote count
        posts = Post.objects.annotate(vote_count=Count('votes')).order_by('-vote_count')
        seralized_posts = [PostSerializer(post).data for post in posts]
        # get all seralized posts
        request = self.factory.get(
            '/api/posts', 
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(seralized_posts, data_view)
        return

class CommentTest(TestCase):
    def setUp(self):
        # set up auth
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user)
        # initialize profiles + posts
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
        )
        self.post1 = Post.objects.create(
            title='faketitle1',
            text='faketext1',
            date=datetime.date(2020, 3, 5),
            author=self.barath,
        )
        self.comment = Comment.objects.create(
            text='fakecomment',
            date=datetime.date(2020, 3, 5),
            post=self.post1,
            author=self.barath
        )
        # upload to database
        self.factory = APIRequestFactory()
        request = self.factory.post('/api/profiles', 
            ProfileSerializer(self.barath).data, 
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        request = self.factory.post('/api/posts', 
            PostSerializer(self.post1).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        request = self.factory.post('/api/comments', 
            CommentSerializer(self.comment).data,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        return 
        
    def test_get_valid_comment(self):
        # get valid comment object
        comment = Comment.objects.get(post=self.post1)
        serialized_comment = CommentSerializer(comment).data
        # get valid query object
        request = self.factory.get(
            '/api/comments',
            {'post_id':self.post1.pk},
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = CommentView.as_view({'get':'list'})(request)
        data_view = raw_view.data[0]
        # should be identical
        self.assertEqual(serialized_comment, data_view)
        return
    
    def test_get_invalid_comment(self):
        # get valid query object
        request = self.factory.get(
            '/api/comments',
            {'post_id':'2'},
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = CommentView.as_view({'get':'list'})(request)
        data_view = raw_view.data
        # should be identical
        self.assertEqual([], data_view)
        return

class MessageTest(TestCase):
    def setUp(self):
        return 
        
    def test_get_valid_message(self):
        return
    
    def test_get_invalid_message(self):
        return 
