from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory

from mist.models import Comment, Favorite, Feature, Mistbox, PostFlag, FriendRequest, MatchRequest, Post, PostVote, Tag, View, Word
from mist.serializers import PostSerializer
from mist.tests.generics import NotificationServiceMock
from mist.views.post import DeleteMistboxPostView, FavoritedPostsView, FeaturedPostsView, MatchedPostsView, MistboxView, Order, PostView, SubmittedPostsView, TaggedPostsView
from users.models import User
from users.tests.generics import create_dummy_user_and_token_given_id


@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class PostTest(TestCase):
    maxDiff = None
    
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    def setUp(self):
        NotificationServiceMock.badges = 0
        NotificationServiceMock.sent_notifications = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

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
        return self.assertEqual(PostSerializer().get_votecount(self.post1), 1)
    
    def test_calculate_commentcount_should_return_number_of_comments(self):
        return self.assertEqual(PostSerializer().get_commentcount(self.post1), 1)
    
    def test_calculate_flagcount_should_return_number_of_flags(self):
        return self.assertEqual(PostSerializer().get_flagcount(self.post1), 1)

    def test_save_should_create_words_in_post(self):
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
    
    def test_save_should_increment_subwords_in_post(self):
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

    def test_save_should_add_to_mistboxes_with_keywords_in_post(self):
        mistbox = Mistbox.objects.create(user=self.user1)
        mistbox.keywords = ['these', 'are', 'cool', 'keywords', 'key']
        mistbox.save()

        post1 = Post.objects.create(
            title='these',
            body='cool',
            author=self.user2,
        )
        post2 = Post.objects.create(
            title='are',
            body='keywords',
            author=self.user2,
        )
        post3 = Post.objects.create(
            title='definitely',
            body='not the droids your looking for',
            author=self.user2,
            location_description="keywords"
        )
        post4 = Post.objects.create(
            title='a',
            body='post that does not contain any of the words',
            author=self.user2,
            location_description="at all"
        )
        test_mistbox = Mistbox.objects.get(id=mistbox.id)

        self.assertIn(post1, test_mistbox.posts.all())
        self.assertIn(post2, test_mistbox.posts.all())
        self.assertIn(post3, test_mistbox.posts.all())
        self.assertNotIn(post4, test_mistbox.posts.all())
        return

    # def test_save_should_send_notifications_with_keywords_in_post(self):
    #     mistbox = Mistbox.objects.create(user=self.user1)
    #     mistbox.keywords = ['these', 'are', 'cool', 'keywords', 'key']
    #     mistbox.save()

    #     Post.objects.create(
    #         title='these are',
    #         body='cool keywords',
    #         author=self.user2,
    #     )

    #     self.assertTrue(NotificationServiceMock.sent_notifications)
    #     self.assertEqual(len(NotificationServiceMock.sent_notifications), 1)
    #     self.assertEqual(NotificationServiceMock.badges, 1)

    def test_save_should_not_add_to_author_mistboxes(self):
        mistbox = Mistbox.objects.create(user=self.user1)
        mistbox.keywords = ['these', 'are', 'cool', 'keywords']
        mistbox.save()

        post1 = Post.objects.create(
            title='these',
            body='cool',
            author=self.user1,
        )
        post2 = Post.objects.create(
            title='are',
            body='keywords',
            author=self.user1,
        )
        test_mistbox = Mistbox.objects.get(id=mistbox.id)

        self.assertNotIn(post1, test_mistbox.posts.all())
        self.assertNotIn(post2, test_mistbox.posts.all())
        return
    
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

    def test_post_should_create_post_without_location(self):
        test_post = Post(
            title='SomeFakeTitle',
            body='ThisPostWillBeTestingCreatingANewPost',
            timestamp=0,
            author=self.user1,
        )
        serialized_post = PostSerializer(test_post).data

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
        self.assertIsNone(response_post.get('location_description'))
        self.assertIsNone(response_post.get('latitude'))
        self.assertIsNone(response_post.get('longitude'))
        self.assertEqual(response_post.get('author'), serialized_post.get('author'))
        self.assertTrue(Post.objects.filter(
            title=test_post.title,
            body=test_post.body,
            location_description__isnull=True,
            latitude__isnull=True,
            longitude__isnull=True,
            timestamp=test_post.timestamp,
            author=test_post.author
        ))
        return

    def test_post_should_create_collectible_given_valid_post_and_collectible(self):
        collectible_type = 1

        test_post = Post(
            title='SomeFakeTitle',
            body='ThisPostWillBeTestingCreatingANewPost',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user1,
            collectible_type=collectible_type,
        )
        serialized_post = PostSerializer(test_post).data

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.filter(
            title=test_post.title,
            body=test_post.body,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            timestamp=test_post.timestamp,
            author=test_post.author,
            collectible_type=collectible_type,
        ))

    def test_post_should_hide_post_given_profanity(self):
        test_post = Post(
            title='fuck you',
            body='fuck fuck fuck shit ass',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user1,
        )
        serialized_post = PostSerializer(test_post).data

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.get(
            body=test_post.body).is_hidden)

    def test_post_should_hide_post_given_hate_speech(self):
        test_post = Post(
            title='nigger',
            body='faggot nigga nigger',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user1,
        )
        serialized_post = PostSerializer(test_post).data

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.get(
            body=test_post.body).is_hidden)
        
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

    def test_get_should_not_return_hidden_posts_for_generic_users(self):
        self.post1.is_hidden = True
        self.post1.save()

        serialized_posts = [
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
            self.assertIn('votecount', response_post)
            self.assertIn('flagcount', response_post)
            self.assertIn('commentcount', response_post)
        return
    
    # def test_get_should_return_correct_votes(self):
    #     serialized_vote = PostVoteSerializer(self.vote).data

    #     request = APIRequestFactory().get(
    #         '/api/posts',
    #         format="json",
    #         HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
    #     )

    #     response = PostView.as_view({'get':'list'})(request)
    #     response_posts = [post_data for post_data in response.data]
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     for post in response_posts:
    #         if post.get('id') == self.vote.post.pk:
    #             vote_ids = [vote.get('id') for vote in post.get('votes')]
    #             correct_vote_id = serialized_vote.get('id')
    #             self.assertTrue(correct_vote_id in vote_ids)
    #     return
    
    # def test_get_should_return_posts_in_vote_minus_flag_order(self):
    #     PostVote.objects.create(voter=self.user1, post=self.post2)
    #     PostVote.objects.create(voter=self.user2, post=self.post2)
    #     PostVote.objects.create(voter=self.user2, post=self.post1)
        
    #     serialized_posts = [
    #         PostSerializer(self.post2).data,
    #         PostSerializer(self.post1).data,
    #         PostSerializer(self.post3).data,
    #     ]
        
    #     request = APIRequestFactory().get(
    #         '/api/posts',
    #         format="json",
    #         HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
    #     )

    #     response = PostView.as_view({'get':'list'})(request)
    #     response_posts = [post_data for post_data in response.data]

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(serialized_posts[0], response_posts[0])
    #     self.assertEqual(serialized_posts[1], response_posts[1])
    #     self.assertEqual(serialized_posts[2], response_posts[2])
    #     return

    def test_get_should_return_posts_given_within_bounds_page_number(self):
        request = APIRequestFactory().get(
            f'/api/posts?page={1}',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_posts)
        return

    def test_get_should_not_return_posts_given_below_lower_bound_page_number(self):
        request = APIRequestFactory().get(
            f'/api/posts?page={0}',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_posts)
        return

    def test_get_should_not_return_posts_given_above_upper_bound_page_number(self):
        request = APIRequestFactory().get(
            f'/api/posts?page={1000}',
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_posts)
        return
    
    def test_get_should_return_posts_in_trending_order_as_default(self):
        self.post1.timestamp = self.post1.creation_time+3600
        self.post2.timestamp = self.post2.creation_time

        self.post1.save()
        self.post2.save()
        
        PostVote.objects.create(voter=self.user1, post=self.post2)
        PostVote.objects.create(voter=self.user2, post=self.post1)       
        PostVote.objects.create(voter=self.user2, post=self.post2)
        
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
        self.assertEqual(serialized_posts[0], response_posts[0])
        self.assertEqual(serialized_posts[1], response_posts[1])
        self.assertEqual(serialized_posts[2], response_posts[2])
        return

    def test_get_should_return_viewed_posts_later_in_the_order(self):
        self.post1.timestamp = self.post1.creation_time+3600
        self.post2.timestamp = self.post2.creation_time

        self.post1.save()
        self.post2.save()

        PostVote.objects.create(voter=self.user2, post=self.post1)
        PostVote.objects.create(voter=self.user3, post=self.post1)
        PostVote.objects.create(voter=self.user1, post=self.post2)
        PostVote.objects.create(voter=self.user2, post=self.post2)

        View.objects.create(post=self.post1, user=self.user1)

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
    
    def test_get_should_return_posts_in_best_order_given_order_parameter(self):
        PostVote.objects.create(voter=self.user2, post=self.post1)
        PostVote.objects.create(voter=self.user2, post=self.post2)
        PostVote.objects.create(voter=self.user3, post=self.post1)
        
        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]
        
        request = APIRequestFactory().get(
            f'/api/posts?order={Order.BEST.value}',
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

    def test_get_should_return_posts_in_trending_order_given_order_parameter(self):
        self.post1.timestamp = self.post1.creation_time+3600
        self.post2.timestamp = self.post2.creation_time

        self.post1.save()
        self.post2.save()
        
        PostVote.objects.create(voter=self.user2, post=self.post1)
        PostVote.objects.create(voter=self.user1, post=self.post2)
        PostVote.objects.create(voter=self.user2, post=self.post2)
        
        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]
        
        request = APIRequestFactory().get(
            f'/api/posts?order={Order.TRENDING.value}',
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

    def test_get_should_return_posts_in_recent_order_given_recent_parameter(self):
        self.post1.creation_time = 4
        self.post1.timestamp = 4
        self.post2.creation_time = 3
        self.post2.timestamp = 3
        self.post3.creation_time = 2
        self.post3.timestamp = 2

        self.post1.save()
        self.post2.save()
        self.post3.save()
        
        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post2).data,
            PostSerializer(self.post3).data,
        ]
        
        request = APIRequestFactory().get(
            f'/api/posts?order={Order.RECENT.value}',
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
        PostFlag.objects.create(flagger=self.user3, post=self.post3)

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
    
    def test_get_should_not_return_posts_with_superuser_flags(self):
        superuser = User.objects.create(
            email="superuser@usc.edu",
            username="superuser",
            date_of_birth=date(2000, 1, 1),
            is_superuser=True,
        )
        serialized_post = PostSerializer(self.post1).data
        PostFlag.objects.create(flagger=superuser, post=self.post1)

        request = APIRequestFactory().get(
            '/api/posts',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = PostView.as_view({'get':'list'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(serialized_post not in response.data)
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
        test_latitude = 1
        test_longitude = 1

        post_from_test_location = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=test_latitude,
            longitude=test_longitude,
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

        serialized_posts_from_usc = [PostSerializer(post_from_test_location).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'latitude': test_latitude,
                'longitude': test_longitude,
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
        test_latitude = 1
        test_longitude = 1
        super_small_radius = 0.00000000001

        post_from_usc_exact = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=test_latitude,
            longitude=test_longitude,
            author=self.user1,
        )
        post_from_usc_inexact = Post.objects.create(
            title='FakeTitleOfUSCPost',
            body='HereIsAPostFromUSC',
            timestamp=0,
            latitude=test_latitude+Decimal(.001),
            longitude=test_longitude+Decimal(.001),
            author=self.user1,
        )
        
        serialized_posts_from_usc = [PostSerializer(post_from_usc_exact).data]

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'latitude': test_latitude,
                'longitude': test_longitude,
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
        serialized_post['is_matched'] = True

        request = APIRequestFactory().get(
            '/api/matched-posts/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchedPostsView.as_view({'get':'list'})(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matched-posts/',
            format='json',
        )
        response = MatchedPostsView.as_view({'get':'list'})(request)

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
        response = FeaturedPostsView.as_view({'get':'list'})(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/featured-posts/',
            format='json',
        )
        response = FeaturedPostsView.as_view({'get':'list'})(request)

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
        response = FavoritedPostsView.as_view({'get':'list'})(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/favorited-posts/',
            format='json',
        )
        response = FavoritedPostsView.as_view({'get':'list'})(request)

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
        response = SubmittedPostsView.as_view({'get':'list'})(request)
        response_post = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post, serialized_post)
        return

    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/submitted-posts/',
            format='json',
        )
        response = SubmittedPostsView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class TaggedPostsViewTest(TestCase):
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

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
            date_of_birth=date(2000, 1, 1),
        )
        self.user3.set_password("TestPassword2@98374")
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user2,
            timestamp=0,
        )

        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            body='FakeTextForSecondPost',
            author=self.user2,
            timestamp=0,
        )

        self.post3 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        self.comment1 = Comment.objects.create(
            post=self.post1,
            body="@testUser2 this is a fake comment",
            author=self.user1,
        )

        self.comment2 = Comment.objects.create(
            post=self.post2,
            body="@testUser2 this is a fake comment",
            author=self.user1,
        )

        self.comment3 = Comment.objects.create(
            post=self.post1,
            body="@testUser3 this is a fake comment",
            author=self.user1,
        )

        Tag.objects.create(
            comment=self.comment1,
            tagging_user=self.user1,
            tagged_user=self.user2,
        )
        Tag.objects.create(
            comment=self.comment2,
            tagging_user=self.user1,
            tagged_user=self.user2,
        )
        Tag.objects.create(
            comment=self.comment3,
            tagging_user=self.user1,
            tagged_user=self.user3,
        )
        return
    
    def test_get_should_return_posts_with_user_in_tagged_comment_given_auth_token(self):
        expected_posts = [PostSerializer(self.post1).data, PostSerializer(self.post2).data]

        request = APIRequestFactory().get(
            '/api/tagged-posts/',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = TaggedPostsView.as_view({'get':'list'})(request)
        response_posts = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response_posts, expected_posts)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/tagged-posts/',
        )
        response = TaggedPostsView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class MistboxViewTest(TestCase):
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

        user1_mistbox = Mistbox.objects.create(user=self.user1)
        user1_mistbox.keywords.append('FakeTitleForFirstPost'.lower())
        user1_mistbox.save()

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user2,
            timestamp=0,
        )

        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            body='FakeTextForSecondPost',
            author=self.user2,
            timestamp=0,
        )

        self.post3 = Post.objects.create(
            title='FakeTitleForThirdPost',
            body='FakeTextForThirdPost',
            author=self.user1,
            timestamp=0,
        )
        
    def test_get_should_return_all_posts_with_keywords_given_no_parameters(self):
        serialized_post = PostSerializer(self.post1).data
        
        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MistboxView.as_view()(request)
        response_mistbox = response.data
        response_posts = response_mistbox.get('posts')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_posts, [serialized_post])
        return

    def test_get_should_not_return_posts_submitted_by_user(self):
        current_user_post = PostSerializer(self.post3).data
        
        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MistboxView.as_view()(request)
        response_mistbox = response.data
        response_posts = response_mistbox.get('posts')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(current_user_post, response_posts)
        return

    def test_get_should_return_404_for_user_without_mistbox(self):        
        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MistboxView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        return

    def test_get_should_empty_list_of_posts_for_user_without_keywords(self):     
        Mistbox.objects.create(user=self.user2)

        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MistboxView.as_view()(request)
        response_mistbox = response.data
        response_posts = response_mistbox.get('posts')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_posts)
        return

    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/mistbox/',
        )
        response = MistboxView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

    def test_get_should_not_return_viewed_posts(self):
        View.objects.create(post=self.post1, user=self.user1)
        
        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MistboxView.as_view()(request)
        response_mistbox = response.data
        response_posts = response_mistbox.get('posts')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_posts)
        return

    def test_get_should_return_posts_in_recency_order(self):
        self.post1.timestamp = 1000
        self.post1.save()
        
        self.post4 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user2,
            timestamp=0,
            creation_time=0,
        )

        serialized_posts = [
            PostSerializer(self.post1).data,
            PostSerializer(self.post4).data,
        ]
        
        request = APIRequestFactory().get(
            '/api/mistbox/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MistboxView.as_view()(request)
        response_mistbox = response.data
        response_posts = response_mistbox.get('posts')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_posts, serialized_posts)
        return

    def test_patch_should_update_keywords_given_user_with_mistbox_and_keywords(self):
        new_keywords = ["new", "keywords"]

        request = APIRequestFactory().patch(
            '/api/mistbox/',
            {
                "keywords": new_keywords
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MistboxView.as_view()(request)
        patched_mistbox = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(patched_mistbox.keywords, new_keywords)
        return

    def test_patch_should_create_mistbox_given_user_without_mistbox_and_keywords(self):
        new_keywords = ["new", "keywords"]

        request = APIRequestFactory().patch(
            '/api/mistbox/',
            {
                "keywords": new_keywords
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MistboxView.as_view()(request)
        matching_mistboxes = Mistbox.objects.filter(user=self.user2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(matching_mistboxes)
        self.assertEqual(matching_mistboxes[0].keywords, new_keywords)
        return
    
    def test_patch_should_create_mistbox_given_user_without_mistbox_and_no_keywords(self):
        new_keywords = []

        request = APIRequestFactory().patch(
            '/api/mistbox/',
            {
                "keywords": new_keywords,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MistboxView.as_view()(request)
        matching_mistboxes = Mistbox.objects.filter(user=self.user2)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(matching_mistboxes)
        self.assertEqual(matching_mistboxes[0].keywords, new_keywords)
        return

    # def test_get_should_not_return_posts_made_over_two_days_ago(self):
    #     beginning_of_time_post = Post.objects.create(
    #         title='FakeTitleForLastPost',
    #         body='FakeTextForLastPost',
    #         author=self.user1,
    #         timestamp=0,
    #         time_created=0,
    #     )
    #     serialized_post = PostSerializer(beginning_of_time_post).data

    #     request = APIRequestFactory().get(
    #         '/api/mistbox-posts/',
    #         format='json',
    #         HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
    #     )
    #     response = MistboxView.as_view()(request)
    #     response_mistboxes = response.data
    #     response_posts = response_mistboxes[0].get('posts')

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertNotIn(serialized_post, response_posts)
    #     return

class DeleteMistboxPostViewTest(TestCase):
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

        user1_mistbox = Mistbox.objects.create(user=self.user1)
        user1_mistbox.keywords.append('FakeTitleForFirstPost'.lower())
        user1_mistbox.save()

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user2,
            timestamp=0,
        )

        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            body='FakeTextForSecondPost',
            author=self.user2,
            timestamp=0,
        )

        self.post3 = Post.objects.create(
            title='FakeTitleForThirdPost',
            body='FakeTextForThirdPost',
            author=self.user1,
            timestamp=0,
        )

    def test_delete_should_return_404_given_nonexistent_mistbox(self):
        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={self.post2.id}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = DeleteMistboxPostView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_should_return_404_given_nonexistent_post_id(self):
        nonexistent_post_id = 1333

        mistbox_before_delete = Mistbox.objects.get(user=self.user1)

        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={nonexistent_post_id}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = DeleteMistboxPostView.as_view()(request)

        mistbox_after_delete = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(mistbox_before_delete, mistbox_after_delete)

    def test_delete_should_return_404_given_opened_post_not_in_mistbox(self):
        mistbox_before_delete = Mistbox.objects.get(user=self.user1)

        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={self.post2.id}&opened=1',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = DeleteMistboxPostView.as_view()(request)

        mistbox_after_delete = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(mistbox_before_delete, mistbox_after_delete)

    def test_delete_should_return_400_given_opened_post_and_exceeded_daily_limit(self):
        mistbox_before_delete = Mistbox.objects.get(user=self.user1)
        mistbox_before_delete.opens_used_today = Mistbox.MAX_DAILY_SWIPES
        mistbox_before_delete.save()

        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={self.post1.id}&opened=1',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = DeleteMistboxPostView.as_view()(request)

        mistbox_after_delete = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(mistbox_before_delete, mistbox_after_delete)

    def test_delete_should_delete_post_given_unopened_post_and_exceeded_daily_limit(self):
        mistbox_before_delete = Mistbox.objects.get(user=self.user1)
        mistbox_before_delete.opens_used_today = Mistbox.MAX_DAILY_SWIPES
        mistbox_before_delete.save()

        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={self.post1.id}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = DeleteMistboxPostView.as_view()(request)

        mistbox_after_delete = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.post1, mistbox_after_delete.posts.all())
        self.assertEqual(mistbox_before_delete.opens_used_today, mistbox_after_delete.opens_used_today)

    def test_delete_should_delete_post_from_mistbox_given_opened_post_and_below_daily_limit(self):
        mistbox_before_delete = Mistbox.objects.get(user=self.user1)
        
        request = APIRequestFactory().delete(
            f'api/delete-mistbox-posts/?post={self.post1.id}&opened=1',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = DeleteMistboxPostView.as_view()(request)
        mistbox_after_delete = Mistbox.objects.get(user=self.user1)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.post1, mistbox_after_delete.posts.all())
        self.assertEqual(mistbox_before_delete.opens_used_today+1, mistbox_after_delete.opens_used_today)