from base64 import b64decode
from datetime import datetime
from decimal import Decimal
import random
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate
from mist.serializers import CommentSerializer, PostSerializer, ProfileSerializer, VoteSerializer, WordSerializer
from mist.views import CommentView, PostView, ProfileView, RegisterView, CreateUserView, ValidateView, VoteView, WordView
from .models import Profile, Post, Comment, Registration, Vote, Word
from django.core.files.uploadedfile import SimpleUploadedFile

# Create your tests here.
class AuthTest(TestCase):
    def test_register_user_valid_email(self):
        # insert user to database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous1@usc.edu',
            },
            format='json',
        )
        raw_view = RegisterView.as_view()(response)
        # insertion should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_201_CREATED)
        # should be one registration request in the DB
        requests = Registration.objects.filter(
            email='anonymous1@usc.edu')
        self.assertEqual(len(requests), 1)
        return
    
    def test_register_user_invalid_email(self):
        # insert user to database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous1',
            },
            format='json',
        )
        raw_view = RegisterView.as_view()(response)
        # insertion should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        # should be one registration request in the DB
        requests = Registration.objects.filter(
            email='anonymous1')
        self.assertEqual(len(requests), 0)
        return
    
    def test_validate_user_valid_code(self):
        # registration request
        code = f'{random.randint(0, 999_999):06}'
        registration = Registration(
            email='anonymous2@usc.edu',
            code=code,
            code_time=datetime.now().timestamp(),
            validation_time=None,
            validated=False,
        )
        registration.save()
        # test validation
        factory = APIRequestFactory()
        response = factory.post('api-validate/',
            {
                'email':'anonymous2@usc.edu',
                'code':code,
            },
            format='json',
        )
        raw_view = ValidateView.as_view()(response)
        # http should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        # registration should be validated
        registration = Registration.objects.filter(
            email='anonymous2@usc.edu')[0]
        self.assertTrue(registration.validated)
        return
    
    def test_validate_user_invalid_code(self):
        # registration request
        code = f'{random.randint(0, 999_999):06}'
        registration = Registration(
            email='anonymous2@usc.edu',
            code=code,
            code_time=datetime.now().timestamp(),
            validation_time=None,
            validated=False,
        )
        registration.save()
        # test validation
        factory = APIRequestFactory()
        response = factory.post('api-validate/',
            {
                'email':'anonymous2@usc.edu',
                'code':int(code)+1,
            },
            format='json',
        )
        raw_view = ValidateView.as_view()(response)
        # http should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        # registration should be validated
        registration = Registration.objects.filter(
            email='anonymous2@usc.edu')[0]
        self.assertFalse(registration.validated)
        return

    def test_create_user_valid_email(self):
        # validate email
        Registration.objects.create(
            email='anonymous2@usc.edu',
            code=f'{random.randint(0, 999_999):06}',
            code_time=datetime.now().timestamp(),
            validated=True,
            validation_time=datetime.now().timestamp(),
        )
        # you should be able to sign up with this email
        factory = APIRequestFactory()
        response = factory.post('api-create-user/',
            {
                'email':'anonymous2@usc.edu',
                'username':'mous2',
                'password':'anon52349',
                'first_name':'anony',
                'last_name':'mous',
            },
            format='json',
        )
        # you should be able to signup with a validated email
        raw_view = CreateUserView.as_view()(response)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        return
    
    def test_create_user_invalid_email(self):
        # validate email
        Registration.objects.create(
            email='anonymous2@usc.edu',
            code=f'{random.randint(0, 999_999):06}',
            code_time=datetime.now().timestamp(),
            validated=True,
            validation_time=datetime.now().timestamp(),
        )
        # you should be able to sign up with this email
        factory = APIRequestFactory()
        response = factory.post('api-create-user/',
            {
                'email':'anonymous1@usc.edu',
                'username':'mous2',
                'password':'anon52349',
                'first_name':'anony',
                'last_name':'mous',
            },
            format='json',
        )
        # you should be able to signup with a validated email
        raw_view = CreateUserView.as_view()(response)
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        return

    def test_obtain_token_valid_user(self):
        user = User(
            email='anonymous3@usc.edu',
            username='anonymous3',
        )
        user.set_password('fakepass12345')
        user.save()
        # generate auth token
        factory = APIRequestFactory()
        response = factory.post('api-token/',
            {
                'username':'anonymous3', 
                'password':'fakepass12345',
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        # generation should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        return
    
    def test_obtain_token_invalid_user(self):
        # generate auth token
        factory = APIRequestFactory()
        response = factory.post('api-token/',
            {
                'username':'anonymous3', 
                'password':'fakepass12345',
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        # generation should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        return

class ProfileTest(TestCase):
    def setUp(self):
        # set up auth
        self.user1 = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user1)
        self.user2 = User.objects.create(username='kevinsun2', 
            password='kevinsun2')
        Token.objects.create(user=self.user2)
        # initialize profiles
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
            user=self.user1,
        )
        self.adam = Profile.objects.create(
            username='adamnovak',
            first_name='adam',
            last_name='novak',
            user=self.user2,
        )
        # upload to database
        self.factory = APIRequestFactory()
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
        force_authenticate(request, user=self.user1, token=self.user1.auth_token)
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
        force_authenticate(request, user=self.user1, token=self.user1.auth_token)
        raw_view = ProfileView.as_view({'get':'list'})(request)
        data_view = raw_view.data
        # should be empty
        self.assertEqual([], raw_view.data)
        return

    def test_put_profile_pic(self):
        # get profile with empty picture
        profile = Profile.objects.get(username=self.barath.username)
        # post gif to profile
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        profile.picture = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')
        profile.save()
        serialized_profile = ProfileSerializer(profile)
        # put it in the database
        request = self.factory.put(
            '/api/profiles/{}'.format(profile.pk),
            {
                'username': profile.username,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'pic': serialized_profile.data['picture'],
                'user': profile.user.pk,
            },
            format="json"
        )
        force_authenticate(request, user=self.user1, token=self.user1.auth_token)
        raw_view = ProfileView.as_view({'put':'update'})(request, pk=profile.pk)
        # check sucessful request
        self.assertEqual(raw_view.status_code, status.HTTP_200_OK)
        # check picture exists
        profile_after_request = Profile.objects.get(username=self.barath.username)
        self.assertNotEqual(profile_after_request.picture, None)

class PostTest(TestCase):
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    def setUp(self):
        # set up auth
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user)
        # initialize profiles
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
            user=self.user,
        )
        # initialize posts
        self.post1 = Post.objects.create(
            id='1',
            title='title1',
            text='fake fake text text',
            timestamp=0,
            author=self.barath,
        )
        self.post2 = Post.objects.create(
            id='2',
            title='title2',
            text='real real real stuff',
            timestamp=1,
            author=self.barath,
        )
        # initialize votes
        self.vote1 = Vote.objects.create(
            voter=self.barath,
            post=self.post1,
            timestamp=0,
            rating=10,
        )
        # initialize comments
        self.comment1 = Comment.objects.create(
            id='fakeID',
            text='fakecomment',
            timestamp=1,
            post=self.post1,
            author=self.barath
        )
        # upload to database
        self.factory = APIRequestFactory()
        return
    
    def test_post_calculate_averagerating(self):
        return self.assertEquals(self.post1.calculate_averagerating(), 
            self.vote1.rating)
    
    def test_post_calculate_averagerating(self):
        return self.assertEquals(self.post1.calculate_commentcount(), 1)

    def test_post_create_words(self):
        Post.objects.create(
            id='5',
            title='what',
            text='have never seen this word',
            timestamp=0,
            author=self.barath,
        )
        self.assertTrue(Word.objects.filter(text='what'))
        self.assertTrue(Word.objects.filter(text='have'))
        self.assertTrue(Word.objects.filter(text='never'))
        self.assertTrue(Word.objects.filter(text='seen'))
        self.assertTrue(Word.objects.filter(text='this'))
        self.assertTrue(Word.objects.filter(text='word'))
    
    def test_post_new_post(self):
        # create new post
        test_post = Post(
            id='3',
            title='title3',
            text='real real real stuff3',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=2,
            author=self.barath,
        )
        serialized_post = PostSerializer(test_post).data
        # check if the post exists
        request = self.factory.post(
            '/api/posts',
            serialized_post,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'post':'create'})(request)
        data_view = raw_view.data
        # post should be successful
        self.assertEqual(data_view, serialized_post)
        return
    
    def test_post_new_words(self):
        # create new post
        test_post = Post.objects.create(
            id='3',
            title='title3',
            text='nonexistent',
            timestamp=2,
            author=self.barath,
        )
        test_word = Word(text='nonexistent')
        serialized_word = WordSerializer(test_word).data
        # check if the word exists
        request = self.factory.get(
            '/api/words',
            {
                'text':'nonexistent'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = WordView.as_view()(request)
        self.assertFalse(len(raw_view.data) == 0)
        data_view = raw_view.data[0]
        # get should be successful
        self.assertEqual(data_view, serialized_word)
        return

    def test_get_all_posts(self):
        # order all seralized posts by vote count
        serialized_posts = [PostSerializer(self.post1).data, 
        PostSerializer(self.post2).data]
        # get all seralized posts
        request = self.factory.get(
            '/api/posts', 
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return
    
    def test_get_posts_by_text(self):
        # only self.post1 has "fake" in its text
        serialized_posts = [PostSerializer(self.post1).data]
        # get all posts with "fake" in its text
        request = self.factory.get(
            '/api/posts',
            {
                'text':'fake'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return
    
    def test_get_posts_by_partial_text(self):
        # only self.post1 has "fa" in its text
        serialized_posts = [PostSerializer(self.post1).data]
        # get all posts with "fa" in its text
        request = self.factory.get(
            '/api/posts',
            {
                'text':'fa'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return

    def test_get_posts_by_timestamp(self):
        # only self.post1 has 0 as its timestamp
        serialized_posts = [PostSerializer(self.post1).data]
        # get all posts with 0 as its timestamp
        request = self.factory.get(
            '/api/posts',
            {
                'timestamp': 0,
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return
    
    def test_get_posts_by_latitude_longitude(self):
        # create a post from USC
        usc_post = Post.objects.create(
            id='101',
            title='to that hunk of a man',
            text='adam. i love you',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=2,
            author=self.barath,
        )
        # create a post from the north pole
        Post.objects.create(
            id='100',
            title='to that hunk of a man',
            text='santa. i love you',
            latitude=Decimal(0),
            longitude=Decimal(0),
            timestamp=2,
            author=self.barath,
        )
        # we want the post from usc
        serialized_posts = [
            PostSerializer(usc_post).data]
        # get all posts at USC
        request = self.factory.get(
            '/api/posts',
            {
                'latitude': self.USC_LATITUDE,
                'longitude': self.USC_LONGITUDE,
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return
    
    def test_get_posts_by_loc_description(self):
        # create a post from the north pole
        north_post = Post.objects.create(
            id='100',
            title='to that hunk of a man',
            location_description='north pole',
            text='santa. i love you',
            latitude=Decimal(0),
            longitude=Decimal(0),
            timestamp=2,
            author=self.barath,
        )
        # we want the post from usc
        serialized_posts = [
            PostSerializer(north_post).data]
        # get all posts at USC
        request = self.factory.get(
            '/api/posts',
            {
                'location_description': 'north pole'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return
    
    def test_get_posts_by_partial_loc_description(self):
        # create a post from the north pole
        north_post = Post.objects.create(
            id='100',
            title='to that hunk of a man',
            location_description='north pole',
            text='santa. i love you',
            latitude=Decimal(0),
            longitude=Decimal(0),
            timestamp=2,
            author=self.barath,
        )
        # we want the post from usc
        serialized_posts = [
            PostSerializer(north_post).data]
        # get all posts at USC
        request = self.factory.get(
            '/api/posts',
            {
                'location_description': 'no'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'get':'list'})(request)
        data_view = [post_data for post_data in raw_view.data]
        # should be identical
        self.assertEqual(serialized_posts, data_view)
        return

    def test_get_posts_by_all_combos(self):
        return
    
    def test_overwrite_post(self):
        # create new post
        test_post = self.post2
        test_post.title = "new fake title2"
        serialized_post = PostSerializer(test_post).data
        # check if the post exists
        request = self.factory.post(
            '/api/posts'.format(test_post.id),
            serialized_post,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = PostView.as_view({'post':'update'})(request, pk=2)
        data_view = raw_view.data
        self.assertEqual(serialized_post, data_view)
        return
        
class VoteTest(TestCase):
    def setUp(self):
        # set up auth
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        Token.objects.create(user=self.user)
        # initialize profiles
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
            user=self.user,
        )
        # initialize posts
        self.post1 = Post.objects.create(
            id='1',
            title='title1',
            text='fake fake text text',
            timestamp=0,
            author=self.barath,
        )
        self.post2 = Post.objects.create(
            id='2',
            title='title2',
            text='real real real stuff',
            timestamp=1,
            author=self.barath,
        )
        # upload to database
        self.factory = APIRequestFactory()
        return
    
    def test_post_vote(self):
        # create vote for post1
        vote = Vote(
            voter=self.barath,
            post=self.post1,
            timestamp=2,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote).data
        # post vote to database
        request = self.factory.post(
            '/api/votes',
            serialized_vote,
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = VoteView.as_view({'post':'create'})(request)
        data_view = raw_view.data
        # should be successful (standardizing primary key ID)
        serialized_vote["id"] = data_view["id"]
        self.assertEqual(serialized_vote, data_view)
        return
    
    def test_delete_vote(self):
        # create new vote in the database
        vote = Vote.objects.create(
            voter=self.barath,
            post=self.post2,
            timestamp=2,
            rating=10,
        )
        # delete vote from database
        request = self.factory.delete(
            '/api/votes/{}'.format(vote.pk),
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        VoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)
        votes = Vote.objects.filter(id=vote.pk)
        # vote should not exist in database
        self.assertQuerysetEqual(votes, Vote.objects.none())
        return
    
    def test_get_vote(self):
        # create new vote in the database 
        vote = Vote.objects.create(
            voter=self.barath,
            post=self.post2,
            timestamp=2,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote).data
        # query vote from database
        request = self.factory.get(
            '/api/votes/',
            {
                'username':self.barath.username,
                'post_id':self.post2.pk,
            },
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = VoteView.as_view({'get':'list'})(request)
        data_view = raw_view.data[0]
        # vote 
        self.assertEqual(serialized_vote, data_view)
        return

class FlagTest(TestCase):
    def setUp(self):
        return
    
    def test_post_flag(self):
        return
    
    def test_delete_flag(self):
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
            user=self.user,
        )
        self.post1 = Post.objects.create(
            title='faketitle1',
            text='faketext1',
            timestamp=0,
            author=self.barath,
        )
        self.comment1 = Comment.objects.create(
            id='fakeID',
            text='fakecomment',
            timestamp=1,
            post=self.post1,
            author=self.barath
        )
        # upload to database
        self.factory = APIRequestFactory()
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

class WordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kevinsun', 
            password='kevinsun')
        self.barath = Profile.objects.create(
            username='barathraghavan',
            first_name='barath',
            last_name='raghavan',
            user=self.user,
        )
        self.factory = APIRequestFactory()
        Token.objects.create(user=self.user)

    def test_get_partial_word(self):
        # create post with text staring with "no"
        Post.objects.create(
            id='3',
            title='title3',
            text='nonexistent, non, nope, nob, no',
            timestamp=2,
            author=self.barath,
        )
        # look for words that start with "no"
        request = self.factory.get(
            '/api/words',
            {
                'text':'no'
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        raw_view = WordView.as_view()(request)
        # Five words that start with "no"
        self.assertEqual(len(raw_view.data), 5)
        for word in raw_view.data:
            # you can find "no" in any word
            self.assertNotEqual(word['text'].find('no'), -1)
        return