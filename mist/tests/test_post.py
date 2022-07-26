from datetime import date
from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, Favorite, Feature, PostFlag, FriendRequest, MatchRequest, Post, PostVote, Word
from mist.serializers import PostSerializer
from mist.views.post import FavoritedPostsView, FeaturedPostsView, MatchedPostsView, PostView, SubmittedPostsView

from users.models import User

class PostTest(TestCase):
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    def setUp(self):
        self.user1 = User(
            email='TestUser@usc.edu',
            username='TestUser',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            timestamp=0,
            author=self.user1,
        )
        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            body='FakeTextForSecondPost',
            timestamp=1,
            author=self.user1,
        )
        self.post3 = Post.objects.create(
            title='FakeTitleForThirdPost',
            body='FakeTextForThirdPost',
            timestamp=2,
            author=self.user1,
        )

        self.vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post1,
        )

        self.comment = Comment.objects.create(
            body='FakeTextForComment',
            post=self.post1,
            author=self.user1,
        )

        self.flag = PostFlag.objects.create(
            post=self.post1,
            flagger=self.user1,
        )
        return
    
    def test_calculate_votecount_should_return_votecount(self):
        return self.assertEquals(self.post1.calculate_votecount(), 1)

    def test_calculate_averagerating_should_return_average_rating(self):
        return self.assertEquals(self.post1.calculate_averagerating(), 
            self.vote.rating)
    
    def test_calculate_commentcount_should_return_number_of_comments(self):
        return self.assertEquals(self.post1.calculate_commentcount(), 1)
    
    def test_calculate_flagcount_should_return_number_of_flags(self):
        return self.assertEquals(self.post1.calculate_flagcount(), 1)

    def test_post_should_create_words_in_post(self):
        Post.objects.create(
            title='TitleWord',
            body='StartingTextWord MiddleTextWord NumbersWord123',
            author=self.user1,
        )
        self.assertTrue(Word.objects.filter(text__iexact='TitleWord'))
        self.assertTrue(Word.objects.filter(text__iexact='StartingTextWord'))
        self.assertTrue(Word.objects.filter(text__iexact='MiddleTextWord'))
        self.assertTrue(Word.objects.filter(text__iexact='NumbersWord123'))
        self.assertFalse(Word.objects.filter(text__iexact='ThisWordDoesNotExist'))
        self.assertFalse(Word.objects.filter(text__iexact='NeitherDoesThisOne'))
    
    def test_post_should_increment_subwords_in_post(self):
        Post.objects.create(
            title='w',
            body='wo',
            author=self.user1,
        )
        Post.objects.create(
            title='wor',
            body='word',
            author=self.user1,
        )
        word1 = Word.objects.get(text__iexact='w')
        word2 = Word.objects.get(text__iexact='wo')
        word3 = Word.objects.get(text__iexact='wor')
        word4 = Word.objects.get(text__iexact='word')
        self.assertEqual(word1.calculate_occurrences(), 2)
        self.assertEqual(word2.calculate_occurrences(), 2)
        self.assertEqual(word3.calculate_occurrences(), 1)
        self.assertEqual(word4.calculate_occurrences(), 1)
    
    def test_post_should_create_post_given_valid_post(self):
        test_post = Post(
            title='SomeFakeTitle',
            body='ThisPostWillBeTestingCreatingANewPost',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user1,
        )
        serialized_post = PostSerializer(test_post).data

        self.assertFalse(Post.objects.filter(
            title=test_post.title,
            body=test_post.body,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            timestamp=test_post.timestamp,
            author=test_post.author
        ))

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'post':'create'})(request)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_post.get('title'), serialized_post.get('title'))
        self.assertEqual(response_post.get('body'), serialized_post.get('body'))
        self.assertEqual(response_post.get('timestamp'), serialized_post.get('timestamp'))
        self.assertEqual(response_post.get('latitude'), serialized_post.get('latitude'))
        self.assertEqual(response_post.get('longitude'), serialized_post.get('longitude'))
        self.assertEqual(response_post.get('author'), serialized_post.get('author'))
        self.assertTrue(Post.objects.filter(
            title=test_post.title,
            body=test_post.body,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            timestamp=test_post.timestamp,
            author=test_post.author
        ))
        return
        
    def test_get_should_return_all_posts_given_no_parameters(self):
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_all_computed_properties(self):
        request = APIRequestFactory().get(
            '/api/posts',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for response_post in response_posts:
            self.assertTrue('votecount' in response_post)
            self.assertTrue('commentcount' in response_post)
            self.assertTrue('averagerating' in response_post)
            self.assertTrue('read_only_author' in response_post)
        return
    
    def test_get_should_return_posts_in_vote_minus_flag_order(self):
        PostVote.objects.create(voter=self.user1, post=self.post2)
        PostVote.objects.create(voter=self.user2, post=self.post2)
        PostVote.objects.create(voter=self.user2, post=self.post1)
        
        serialized_posts = [
            PostSerializer(self.post2).data,
            PostSerializer(self.post1).data,
            PostSerializer(self.post3).data,
        ]
        
        request = APIRequestFactory().get(
            '/api/posts',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts[0], response_posts[0])
        self.assertEqual(serialized_posts[1], response_posts[1])
        self.assertEqual(serialized_posts[2], response_posts[2])
        return
    
    def test_get_should_not_return_posts_with_flags_greater_than_square_root_of_votes(self):
        PostFlag.objects.create(flagger=self.user1, post=self.post3)
        PostFlag.objects.create(flagger=self.user2, post=self.post3)

        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post2).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_post_with_matching_id_given_id(self):
        serialized_posts = [
            PostSerializer(self.post1).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'ids': self.post1.id,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_post_with_matching_ids_given_ids(self):
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data,
        ]

        request = APIRequestFactory().get(
            f'/api/posts?ids={self.post1.id}&ids={self.post2.id}',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_word_given_word(self):
        serialized_posts = [PostSerializer(self.post1).data]
        word = self.post1.body.split(' ')[0]
        
        request = APIRequestFactory().get(
            f'/api/posts?words={word}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_words_given_full_words(self):
        serialized_posts = [
            PostSerializer(self.post1).data,
        ]
        word1 = self.post1.body.split(' ')[0]
        word2 = self.post1.title.split(' ')[0]

        request = APIRequestFactory().get(
            f'/api/posts?words={word1}&words={word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
 
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_words_given_partial_words(self):
        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]
        word1 = "Fake"
        word2 = "Text"

        request = APIRequestFactory().get(
            f'/api/posts?words={word1}&words={word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
 
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return

    def test_get_should_return_posts_with_matching_timestamp_given_timestamp(self):
        serialized_posts = [PostSerializer(self.post1).data]

        request = APIRequestFactory().get(
            f'/api/posts?start_timestamp={self.post1.timestamp}&end_timestamp={self.post1.timestamp}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_within_inclusive_timestamp_range_given_timestamp_range(self):
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data]

        request = APIRequestFactory().get(
            f'/api/posts?start_timestamp={self.post1.timestamp}&end_timestamp={self.post2.timestamp}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_within_latitude_longitude_range_given_latitude_longitude(self):
        post_from_usc = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user1,
        )
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            body='HereIsAPostFromTheNorthPole',
            timestamp=0,
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user1,
        )

        serialized_posts_from_usc = [PostSerializer(post_from_usc).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'latitude': self.USC_LATITUDE,
                'longitude': self.USC_LONGITUDE,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_usc, response_posts)
        return
    
    def test_get_should_return_posts_on_exact_coordinates_given_latitude_longitude_radius_zero(self):
        super_small_radius = 0.00000000001

        post_from_usc_exact = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user1,
        )
        post_from_usc_inexact = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=self.USC_LATITUDE+Decimal(.001),
            longitude=self.USC_LONGITUDE+Decimal(.001),
            author=self.user1,
        )
        
        serialized_posts_from_usc = [PostSerializer(post_from_usc_exact).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'latitude': self.USC_LATITUDE,
                'longitude': self.USC_LONGITUDE,
                'radius': super_small_radius,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_usc, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_loc_description_given_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            body='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            timestamp=0,
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user1,
        )

        serialized_posts_from_north_pole = [
            PostSerializer(post_from_north_pole).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'location_description': 'North Pole'
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_north_pole, response_posts)
        return
    
    def test_get_should_return_posts_with_partially_matching_loc_description_given_partial_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            body='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            timestamp=0,
            latitude=Decimal(0),
            longitude=Decimal(0),
            author=self.user1,
        )

        serialized_posts_from_north_pole = [
            PostSerializer(post_from_north_pole).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'location_description': 'North'
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_north_pole, response_posts)
        return
    
    def test_get_should_return_posts_by_current_user_given_current_user_as_author(self):
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'author': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_by_friend_given_friend_as_author(self):
        friend = User.objects.create(
            email='TestFriendEmail@usc.edu',
            username='TestFriend',
            date_of_birth=date(2000, 1, 1),
        )
        friend.set_password("TestFriend@98374")
        friend.save()
        friend_auth_token = Token.objects.create(user=friend)
        FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=friend,
            timestamp=0,
        )
        FriendRequest.objects.create(
            friend_requesting_user=friend,
            friend_requested_user=self.user1,
            timestamp=0,
        )
        serialized_posts = [
            PostSerializer(self.post1).data, 
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'author': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response_posts, serialized_posts)
        return
    
    def test_get_should_return_not_posts_given_stranger_as_author(self):
        stranger = User.objects.create(
            email='TestStranger@usc.edu',
            username='TestStranger',
            date_of_birth=date(2000, 1, 1),
        )
        stranger.set_password("TestStranger@98374")
        stranger.save()
        stranger_auth_token = Token.objects.create(user=stranger)

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'author': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {stranger_auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        return
    
    def test_put_should_update_title_given_serialized_post(self):
        fake_title =  "NewFakeTitleForFirstPost"
        self.post1.title = fake_title
        serialized_post = PostSerializer(self.post1).data

        self.assertFalse(Post.objects.filter(title=fake_title))

        request = APIRequestFactory().put(
            '/api/posts/',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return
    
    def test_put_should_update_text_given_serialized_post(self):
        fake_text = "NewFakeTextForFirstPost"
        self.post1.body = fake_text
        serialized_post = PostSerializer(self.post1).data

        self.assertFalse(Post.objects.filter(body=fake_text))

        request = APIRequestFactory().put(
            '/api/posts/',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(body=fake_text))
        return

    def test_patch_should_update_title_given_valid_post_title(self):
        fake_title = 'NewFakeTitleForFirstPost'

        self.assertFalse(Post.objects.filter(title=fake_title))

        request = APIRequestFactory().patch(
            '/api/posts/',
            {
                'title': fake_title,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post.get('title'), fake_title)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return

    def test_patch_should_update_text_given_valid_post_text(self):
        fake_text = 'NewFakeTextForFirstPost'

        self.assertFalse(Post.objects.filter(body=fake_text))

        request = APIRequestFactory().patch(
            '/api/posts/',
            {
                'body': fake_text,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('body'), fake_text)
        self.assertTrue(Post.objects.filter(body=fake_text))
        return

    def test_delete_should_delete_post(self):
        self.assertTrue(Post.objects.filter(pk=self.post1.pk))

        request = APIRequestFactory().delete('/api/posts/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostView.as_view({'delete':'destroy'})(request, pk=self.post1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post1.pk))
        return

class MatchedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        MatchRequest.objects.create(
            match_requesting_user=self.user2,
            match_requested_user=self.user1,
            post=self.post,
            timestamp=0,
        )

        MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        return

    def test_get_should_return_all_matched_posts_given_no_parameters(self):
        serialized_post = PostSerializer(self.post).data

        request = APIRequestFactory().get(
            '/api/matched-posts/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchedPostsView.as_view()(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matched-posts/',
            format='json',
        )
        response = MatchedPostsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class FeaturedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        Feature.objects.create(
            post=self.post,
            timestamp=0,
        )
        return

    def test_get_should_return_all_featured_posts_given_no_parameters(self):
        serialized_post = PostSerializer(self.post).data

        request = APIRequestFactory().get(
            '/api/featured-posts/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeaturedPostsView.as_view()(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/featured-posts/',
            format='json',
        )
        response = FeaturedPostsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class FavoritedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        Favorite.objects.create(
            favoriting_user=self.user1,
            post=self.post,
            timestamp=0,
        )
        return

    def test_get_should_return_all_favorited_posts_given_no_parameters(self):
        serialized_post = PostSerializer(self.post).data

        request = APIRequestFactory().get(
            '/api/favorited-posts/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoritedPostsView.as_view()(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/favorited-posts/',
            format='json',
        )
        response = FavoritedPostsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class SubmittedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )
        return
    
    def test_get_should_return_all_submitted_posts_given_no_parameters(self):
        serialized_post = PostSerializer(self.post).data
        
        request = APIRequestFactory().get(
            '/api/submitted-posts/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = SubmittedPostsView.as_view()(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return

    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/submitted-posts/',
            format='json',
        )
        response = SubmittedPostsView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return