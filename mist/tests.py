from decimal import Decimal
from django.test import TestCase
from users.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate
from mist.serializers import CommentSerializer, FlagSerializer, PostSerializer, VoteSerializer
from mist.views import CommentView, FlagView, PostView, VoteView, WordView
from .models import Flag, Post, Comment, Vote, Word

class PostTest(TestCase):
    maxDiff = None

    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        Token.objects.create(user=self.user)

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )
        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            text='FakeTextForSecondPost',
            author=self.user,
        )

        self.vote = Vote.objects.create(
            voter=self.user,
            post=self.post1,
        )

        self.comment = Comment.objects.create(
            text='FakeTextForComment',
            post=self.post1,
            author=self.user,
        )
        return
    
    def test_post_calculate_averagerating(self):
        return self.assertEquals(self.post1.calculate_averagerating(), 
            self.vote.rating)
    
    def test_post_calculate_averagerating(self):
        return self.assertEquals(self.post1.calculate_commentcount(), 1)

    def test_post_create_words(self):
        Post.objects.create(
            title='TitleWord',
            text='StartingTextWord MiddleTextWord NumbersWord123',
            author=self.user,
        )
        self.assertTrue(Word.objects.filter(text='TitleWord'))
        self.assertTrue(Word.objects.filter(text='StartingTextWord'))
        self.assertTrue(Word.objects.filter(text='MiddleTextWord'))
        self.assertTrue(Word.objects.filter(text='NumbersWord123'))
        self.assertFalse(Word.objects.filter(text='ThisWordDoesNotExist'))
        self.assertFalse(Word.objects.filter(text='NeitherDoesThisOne'))
    
    def test_post_new_post(self):
        test_post = Post(
            title='SomeFakeTitle',
            text='ThisPostWillBeTestingCreatingANewPost',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user,
        )
        serialized_post = PostSerializer(test_post).data

        self.assertFalse(Post.objects.filter(
            title=test_post.title,
            text=test_post.text,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            author=test_post.author
        ))

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'post':'create'})(request)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_post.get('title'), serialized_post.get('title'))
        self.assertEqual(response_post.get('text'), serialized_post.get('text'))
        self.assertEqual(response_post.get('latitude'), serialized_post.get('latitude'))
        self.assertEqual(response_post.get('longitude'), serialized_post.get('longitude'))
        self.assertEqual(response_post.get('author'), serialized_post.get('author'))
        self.assertTrue(Post.objects.filter(
            title=test_post.title,
            text=test_post.text,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            author=test_post.author
        ))
        return
    
    def test_post_new_words(self):
        self.assertFalse(Word.objects.filter(text='ThisTextNowExists'))
        test_post = Post.objects.create(
            title='SomeFakeTitle',
            text='ThisTextNowExists',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user,
        )

        request = APIRequestFactory().get(
            '/api/words',
            {
                'text': test_post.text,
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data[0].get('text'), 'ThisTextNowExists')
        self.assertTrue(Word.objects.filter(text='ThisTextNowExists'))
        return

    def test_get_all_posts(self):
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts', 
            format="json"
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_get_posts_by_text(self):
        serialized_posts = [PostSerializer(self.post1).data]
        
        request = APIRequestFactory().get(
            '/api/posts',
            {
                'text': self.post1.text,
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_get_posts_by_partial_text(self):
        serialized_posts = [PostSerializer(self.post1).data]

        mid_point_of_text = len(self.post1.text)//2
        half_of_post_text = self.post1.text[mid_point_of_text:]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'text': half_of_post_text,
            },
            format='json'
        )
 
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return

    def test_get_posts_by_timestamp(self):
        serialized_posts = [PostSerializer(self.post1).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'timestamp': self.post1.timestamp,
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_get_posts_by_latitude_longitude(self):
        post_from_usc = Post.objects.create(
            title='FakeTitleOfUSCPost',
            text='HereIsAPostFromUSC',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user,
        )
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user,
        )

        serialized_posts_from_usc = [PostSerializer(post_from_usc).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'latitude': self.USC_LATITUDE,
                'longitude': self.USC_LONGITUDE,
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts_from_usc, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_get_posts_by_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user,
        )

        serialized_posts_from_north_pole = [
            PostSerializer(post_from_north_pole).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'location_description': 'North Pole'
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts_from_north_pole, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_get_posts_by_partial_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user,
        )

        serialized_posts_from_north_pole = [
            PostSerializer(post_from_north_pole).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'location_description': 'North'
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for serialized_post, response_post in zip(serialized_posts_from_north_pole, response_posts):
            self.assertDictEqual(serialized_post, response_post)
        return
    
    def test_put_post_title(self):
        fake_title =  "NewFakeTitleForFirstPost"
        self.post1.title = fake_title
        serialized_post = PostSerializer(self.post1).data

        self.assertFalse(Post.objects.filter(title=fake_title))

        request = APIRequestFactory().put(
            '/api/posts/',
            serialized_post,
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return
    
    def test_put_post_text(self):
        fake_text = "NewFakeTextForFirstPost"
        self.post1.text = fake_text
        serialized_post = PostSerializer(self.post1).data

        self.assertFalse(Post.objects.filter(text=fake_text))

        request = APIRequestFactory().put(
            '/api/posts/',
            serialized_post,
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(text=fake_text))
        return

    def test_patch_valid_post_title(self):
        fake_title = 'NewFakeTitleForFirstPost'

        self.assertFalse(Post.objects.filter(title=fake_title))

        request = APIRequestFactory().patch(
            '/api/posts/',
            {
                'title': fake_title,
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post.get('title'), fake_title)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return

    def test_patch_post_text(self):
        fake_text = 'NewFakeTextForFirstPost'

        self.assertFalse(Post.objects.filter(text=fake_text))

        request = APIRequestFactory().patch(
            '/api/posts/',
            {
                'text': fake_text,
            },
            format='json'
        )

        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), fake_text)
        self.assertTrue(Post.objects.filter(text=fake_text))
        return

    def test_delete_post(self):
        self.assertTrue(Post.objects.filter(pk=self.post1.pk))

        request = APIRequestFactory().delete('/api/posts/')
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = PostView.as_view({'delete':'destroy'})(request, pk=self.post1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post1.pk))
        return
        
class VoteTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )
        return
    
    def test_post_vote(self):
        vote = Vote(
            voter=self.user,
            post=self.post,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote).data

        self.assertFalse(Vote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            rating=vote.rating,
        ))

        request = APIRequestFactory().post(
            '/api/votes',
            serialized_vote,
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = VoteView.as_view({'post':'create'})(request)

        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_vote.get('voter'), serialized_vote.get('voter'))
        self.assertEqual(response_vote.get('post'), serialized_vote.get('post'))
        self.assertEqual(response_vote.get('rating'), serialized_vote.get('rating'))
        self.assertTrue(Vote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            rating=vote.rating,
        ))
        return
    
    def test_delete_vote(self):
        vote = Vote.objects.create(
            voter=self.user,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/')
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = VoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vote.objects.filter(pk=vote.pk))
        return
    
    def test_get_vote(self):
        vote = Vote.objects.create(
            voter=self.user,
            post=self.post,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote).data
        self.assertTrue(Vote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            rating=vote.rating,
        ))

        request = APIRequestFactory().get(
            '/api/votes/',
            {
                'username': self.user.username,
                'post_id': self.post.pk,
            },
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = VoteView.as_view({'get':'list'})(request)

        response_vote = response.data[0]
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(serialized_vote, response_vote)
        return

class FlagTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )
        return
    
    def test_post_flag(self):
        flag = Flag(
            flagger=self.user,
            post=self.post
        )
        serialized_flag = FlagSerializer(flag).data
        self.assertFalse(Flag.objects.filter(
            flagger=flag.flagger,
            post=flag.post
        ))

        request = APIRequestFactory().post(
            '/api/flags/',
            serialized_flag,
            format='json',
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = FlagView.as_view({'post':'create'})(request)
        response_flag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_flag.get('flagger'), serialized_flag.get('flagger'))
        self.assertEqual(response_flag.get('post'), serialized_flag.get('post'))
        self.assertTrue(Flag.objects.filter(
            flagger=flag.flagger,
            post=flag.post
        ))
        return
    
    def test_delete_flag(self):
        flag = Flag.objects.create(
            flagger=self.user,
            post=self.post,
        )
        self.assertTrue(Flag.objects.filter(pk=flag.pk))
        request = APIRequestFactory().delete('/api/flags/')
        response = FlagView.as_view({'delete':'destroy'})(request, pk=flag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Flag.objects.filter(pk=flag.pk))
        return

class CommentTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )

        self.comment = Comment.objects.create(
            text='FakeTextForComment',
            post=self.post,
            author=self.user
        )

        self.unused_post_id = 155
        return 
        
    def test_get_valid_comment(self):
        serialized_comment = CommentSerializer(self.comment).data

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post_id':self.post.pk
            },
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(serialized_comment, response_comment)
        self.assertIn('author_username', response_comment)
        return
    
    def test_get_invalid_comment(self):
        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post_id': self.unused_post_id,
            },
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_comment)
        return

    def test_post_valid_comment(self):
        test_comment = Comment(
            text='FakeTextForTestComment',
            post=self.post,
            author=self.user
        )
        serialized_comment = CommentSerializer(test_comment).data

        self.assertFalse(Comment.objects.filter(
            text=test_comment.text,
            post=test_comment.post,
            author=test_comment.author))

        request = APIRequestFactory().post(
            '/api/comments/',
            serialized_comment,
            format="json"
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = CommentView.as_view({'post':'create'})(request)
        response_comment = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_comment.get('text'), serialized_comment.get('text'))
        self.assertEqual(response_comment.get('post'), serialized_comment.get('post'))
        self.assertEqual(response_comment.get('author'), serialized_comment.get('author'))
        self.assertTrue(Comment.objects.filter(
            text=test_comment.text,
            post=test_comment.post,
            author=test_comment.author))
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
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        Token.objects.create(user=self.user)

    def test_get_partial_word(self):
        word_to_search = 'Fake'
        self.assertFalse(Word.objects.filter(text__contains=word_to_search))
        Post.objects.create(
            title='FakeTitleForFakePost',
            text='FakeTextForFakePost',
            author=self.user,
        )

        request = APIRequestFactory().get(
            '/api/words',
            {
                'text': word_to_search,
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertFalse(word.get('text').find(word_to_search), -1)
        self.assertTrue(Word.objects.filter(text__contains=word_to_search))
        return
    
    def test_get_full_word(self):
        word_to_search = 'FakeTitleForFakePost'
        self.assertFalse(Word.objects.filter(text__contains=word_to_search))
        Post.objects.create(
            title='FakeTitleForFakePost',
            text='FakeTextForFakePost',
            author=self.user,
        )

        request = APIRequestFactory().get(
            '/api/words',
            {
                'text': word_to_search,
            },
            format='json'
        )
        force_authenticate(request, user=self.user, token=self.user.auth_token)
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertFalse(word.get('text').find(word_to_search), -1)
        self.assertTrue(Word.objects.filter(text__contains=word_to_search))
        return