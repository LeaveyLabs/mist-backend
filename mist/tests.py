from decimal import Decimal
from django.test import TestCase
from mist.accessory_views import FavoritedPostsView, FeaturedPostsView, FriendshipView, MatchView, MatchedPostsView, SubmittedPostsView
from users.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.serializers import BlockSerializer, CommentSerializer, FavoriteSerializer, FeatureSerializer, FlagSerializer, FriendRequestSerializer, MatchRequestSerializer, MessageSerializer, PostSerializer, TagSerializer, VoteSerializer
from mist.model_views import BlockView, CommentView, FavoriteView, FeatureView, FlagView, FriendRequestView, MatchRequestView, MessageView, PostView, TagView, VoteView, WordView
from users.serializers import ReadOnlyUserSerializer
from .models import Block, Favorite, Feature, Flag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, Vote, Word

# MODEL VIEWS

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
        self.auth_token = Token.objects.create(user=self.user)

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            timestamp=0,
            author=self.user,
        )
        self.post2 = Post.objects.create(
            title='FakeTitleForSecondPost',
            text='FakeTextForSecondPost',
            timestamp=1,
            author=self.user,
        )
        self.post3 = Post.objects.create(
            title='FakeTitleForThirdPost',
            text='FakeTextForThirdPost',
            timestamp=2,
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
    
    def test_calculate_averagerating_should_return_average_rating(self):
        return self.assertEquals(self.post1.calculate_averagerating(), 
            self.vote.rating)
    
    def test_calculate_commentcount_should_return_number_of_comments(self):
        return self.assertEquals(self.post1.calculate_commentcount(), 1)

    def test_post_should_create_words_in_post(self):
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
    
    def test_post_should_create_post_given_valid_post(self):
        test_post = Post(
            title='SomeFakeTitle',
            text='ThisPostWillBeTestingCreatingANewPost',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user,
        )
        serialized_post = PostSerializer(test_post).data

        self.assertFalse(Post.objects.filter(
            title=test_post.title,
            text=test_post.text,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            timestamp=test_post.timestamp,
            author=test_post.author
        ))

        request = APIRequestFactory().post(
            '/api/posts',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = PostView.as_view({'post':'create'})(request)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_post.get('title'), serialized_post.get('title'))
        self.assertEqual(response_post.get('text'), serialized_post.get('text'))
        self.assertEqual(response_post.get('timestamp'), serialized_post.get('timestamp'))
        self.assertEqual(response_post.get('latitude'), serialized_post.get('latitude'))
        self.assertEqual(response_post.get('longitude'), serialized_post.get('longitude'))
        self.assertEqual(response_post.get('author'), serialized_post.get('author'))
        self.assertTrue(Post.objects.filter(
            title=test_post.title,
            text=test_post.text,
            latitude=test_post.latitude,
            longitude=test_post.longitude,
            timestamp=test_post.timestamp,
            author=test_post.author
        ))
        return
    
    def test_post_should_create_words_in_post_given_valid_post(self):
        self.assertFalse(Word.objects.filter(text='ThisTextNowExists'))
        test_post = Post.objects.create(
            title='SomeFakeTitle',
            text='ThisTextNowExists',
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            timestamp=0,
            author=self.user,
        )

        request = APIRequestFactory().get(
            '/api/words',
            {
                'text': test_post.text,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        self.assertEqual(response.data[0].get('text'), 'ThisTextNowExists')
        self.assertTrue(Word.objects.filter(text='ThisTextNowExists'))
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_text_given_text(self):
        serialized_posts = [PostSerializer(self.post1).data]
        
        request = APIRequestFactory().get(
            f'/api/posts?text={self.post1.text}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_with_partially_matching_text_given_partial_text(self):
        serialized_posts = [PostSerializer(self.post1).data]

        mid_point_of_text = len(self.post1.text)//2
        half_of_post_text = self.post1.text[mid_point_of_text:]

        request = APIRequestFactory().get(
            f'/api/posts?text={half_of_post_text}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(serialized_posts, response_posts)
        return
    
    def test_get_should_return_posts_within_latitude_longitude_range_given_latitude_longitude(self):
        post_from_usc = Post.objects.create(
            title='FakeTitleOfUSCPost',
            text='HereIsAPostFromUSC',
            timestamp=0,
            latitude=self.USC_LATITUDE,
            longitude=self.USC_LONGITUDE,
            author=self.user,
        )
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            timestamp=0,
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
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_usc, response_posts)
        return
    
    def test_get_should_return_posts_with_matching_loc_description_given_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            timestamp=0,
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
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'get':'list'})(request)
        response_posts = [post_data for post_data in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_posts_from_north_pole, response_posts)
        return
    
    def test_get_should_return_posts_with_partially_matching_loc_description_given_partial_loc_description(self):
        post_from_north_pole = Post.objects.create(
            title='FakeTitleOfNorthPolePost',
            text='HereIsAPostFromTheNorthPole',
            location_description='North Pole',
            timestamp=0,
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
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
                'author': self.user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
        )
        friend.set_password("TestFriend@98374")
        friend.save()
        friend_auth_token = Token.objects.create(user=friend)
        FriendRequest.objects.create(
            friend_requesting_user=self.user,
            friend_requested_user=friend,
            timestamp=0,
        )
        FriendRequest.objects.create(
            friend_requesting_user=friend,
            friend_requested_user=self.user,
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
                'author': self.user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
        )
        stranger.set_password("TestStranger@98374")
        stranger.save()
        stranger_auth_token = Token.objects.create(user=stranger)

        request = APIRequestFactory().get(
            '/api/posts',
            {
                'author': self.user.pk,
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return
    
    def test_put_should_update_text_given_serialized_post(self):
        fake_text = "NewFakeTextForFirstPost"
        self.post1.text = fake_text
        serialized_post = PostSerializer(self.post1).data

        self.assertFalse(Post.objects.filter(text=fake_text))

        request = APIRequestFactory().put(
            '/api/posts/',
            serialized_post,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'put':'update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_post, response_post)
        self.assertTrue(Post.objects.filter(text=fake_text))
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )

        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        response_post = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_post.get('title'), fake_title)
        self.assertTrue(Post.objects.filter(title=fake_title))
        return

    def test_patch_should_update_text_given_valid_post_text(self):
        fake_text = 'NewFakeTextForFirstPost'

        self.assertFalse(Post.objects.filter(text=fake_text))

        request = APIRequestFactory().patch(
            '/api/posts/',
            {
                'text': fake_text,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = PostView.as_view({'patch':'partial_update'})(request, pk=self.post1.pk)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('text'), fake_text)
        self.assertTrue(Post.objects.filter(text=fake_text))
        return

    def test_delete_should_delete_post(self):
        self.assertTrue(Post.objects.filter(pk=self.post1.pk))

        request = APIRequestFactory().delete('/api/posts/', HTTP_AUTHORIZATION=f'Token {self.auth_token}',)
        response = PostView.as_view({'delete':'destroy'})(request, pk=self.post1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post1.pk))
        return
        
class VoteTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user1.set_password("TestPassword@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUse2r',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )
        return
    
    def test_post_should_create_vote_given_valid_vote(self):
        vote = Vote(
            voter=self.user1,
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
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
    
    def test_delete_should_delete_vote(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vote.objects.filter(pk=vote.pk))
        return
    
    def test_get_should_return_votes_by_voter_on_post_given_voter_and_post(self):
        vote1 = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            timestamp=0,
            rating=10,
        )
        vote2 = Vote.objects.create(
            voter=self.user2,
            post=self.post,
            timestamp=0,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote1).data
        self.assertTrue(Vote.objects.filter(
            voter=vote1.voter,
            post=vote1.post,
            timestamp=vote1.timestamp,
            rating=vote1.rating,
        ))
        self.assertTrue(Vote.objects.filter(
            voter=vote2.voter,
            post=vote2.post,
            timestamp=vote2.timestamp,
            rating=vote2.rating,
        ))

        request = APIRequestFactory().get(
            '/api/votes/',
            {
                'voter': vote1.voter.pk,
                'post': vote1.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VoteView.as_view({'get':'list'})(request)
        response_vote = response.data[0]

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_vote, response_vote)
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
        self.auth_token = Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )

        self.comment = Comment.objects.create(
            text='FakeTextForComment',
            post=self.post,
            author=self.user,
            timestamp=0,
        )

        self.unused_post_id = 155
        return 
        
    def test_get_should_return_comment_given_post_pk(self):
        serialized_comment = CommentSerializer(self.comment).data

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post':self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_comment, response_comment)
        self.assertIn('author_username', response_comment)
        return
    
    def test_get_should_not_return_comment_given_invalid_post_pk(self):
        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.unused_post_id,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_comment)
        return

    def test_post_should_create_comment_given_valid_comment(self):
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
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
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

    def test_delete_should_delete_comment(self):
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk))

        request = APIRequestFactory().delete('/api/comment/', HTTP_AUTHORIZATION=f'Token {self.auth_token}')
        response = CommentView.as_view({'delete':'destroy'})(request, pk=self.comment.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk))
        return

class FlagTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        self.auth_token = Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user,
        )
        return

    def test_get_should_return_flag_given_valid_flagger(self):
        flag = Flag.objects.create(
            flagger=self.user,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = FlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'flagger': flag.flagger.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = FlagView.as_view({'get':'list'})(request)
        response_flag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_flag, serialized_flag)
        return
    
    def test_get_should_not_return_flag_given_invalid_flagger(self):
        request = APIRequestFactory().get(
            '/api/flags',
            {
                'flagger': self.user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = FlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_get_should_return_flag_given_valid_post(self):
        flag = Flag.objects.create(
            flagger=self.user,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = FlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'post': flag.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = FlagView.as_view({'get':'list'})(request)
        response_flag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_flag, serialized_flag)
        return
    
    def test_get_should_not_return_flag_given_invalid_post(self):
        request = APIRequestFactory().get(
            '/api/flags',
            {
                'post': self.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = FlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_post_should_create_flag_given_valid_flag(self):
        flag = Flag(
            flagger=self.user,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = FlagSerializer(flag).data

        self.assertFalse(Flag.objects.filter(
            flagger=flag.flagger,
            post=flag.post,
            timestamp=flag.timestamp,
        ))

        request = APIRequestFactory().post(
            '/api/flags/',
            serialized_flag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = FlagView.as_view({'post':'create'})(request)
        response_flag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_flag.get('flagger'), serialized_flag.get('flagger'))
        self.assertEqual(response_flag.get('post'), serialized_flag.get('post'))
        self.assertTrue(Flag.objects.filter(
            flagger=flag.flagger,
            post=flag.post,
            timestamp=flag.timestamp,
        ))
        return
    
    def test_delete_should_delete_flag(self):
        flag = Flag.objects.create(
            flagger=self.user,
            post=self.post,
        )
        self.assertTrue(Flag.objects.filter(pk=flag.pk))
        request = APIRequestFactory().delete('/api/flags/', HTTP_AUTHORIZATION=f'Token {self.auth_token}')
        response = FlagView.as_view({'delete':'destroy'})(request, pk=flag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Flag.objects.filter(pk=flag.pk))
        return

class TagTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )

        self.unused_pk = 151
        return
    
    def test_get_should_return_tag_given_valid_tagged_user(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user1,
            tagging_user=self.user2,
            timestamp=0,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagged_user': tag.tagged_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tag, serialized_tag)
        return
    
    def test_get_should_not_return_tag_given_invalid_tagged_user(self):
        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagged_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_tags)
        return
    
    def test_get_should_return_tag_given_valid_tagging_user(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user1,
            tagging_user=self.user2,
            timestamp=0,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagging_user': tag.tagging_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tag, serialized_tag)
        return

    def test_get_should_not_return_tag_given_invalid_tagging_user(self):
        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagging_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_tags)
        return

    def test_post_should_create_tag_given_valid_tag(self):
        tag = Tag(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)
        response_tag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_tag.get('post'), serialized_tag.get('post'))
        self.assertEqual(response_tag.get('tagged_user'), serialized_tag.get('tagged_user'))
        self.assertEqual(response_tag.get('tagging_user'), serialized_tag.get('tagging_user'))
        self.assertTrue(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        ))
        return
    
    def test_post_should_not_create_tag_given_invalid_tag(self):
        tag = Tag(
            post=self.post,
            tagging_user=self.user1,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
        ))

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
        ))
        return
    
    def test_delete_should_delete_tag(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user2,
            tagging_user=self.user1,            
        )

        self.assertTrue(Tag.objects.filter(pk=tag.pk))

        request = APIRequestFactory().delete('/api/tags/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = TagView.as_view({'delete':'destroy'})(request, pk=tag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=tag.pk))
        return

class BlockTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )

        self.unused_pk = 151
        return
    
    def test_get_should_return_block_given_valid_blocked_user(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocked_user': block.blocked_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_block = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_block, serialized_block)
        return
    
    def test_get_should_not_return_block_given_invalid_blocked_user(self):
        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocked_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_blocks = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_blocks)
        return
    
    def test_get_should_return_block_given_valid_blocking_user(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocking_user': block.blocking_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_block = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_block, serialized_block)
        return
    
    def test_get_should_not_return_block_given_invalid_blocking_user(self):
        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocking_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_blocks = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_blocks)
        return

    def test_post_should_create_block_given_valid_block(self):
        block = Block(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
            blocked_user=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/blocks',
            serialized_block,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'post':'create'})(request)
        response_block = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_block.get('blocking_user'), serialized_block.get('blocking_user'))
        self.assertEqual(response_block.get('blocked_user'), serialized_block.get('blocked_user'))
        self.assertTrue(Block.objects.filter(
            blocking_user=self.user1,
            blocked_user=self.user2,
        ))
        return
    
    def test_post_should_not_create_block_given_invalid_block(self):
        block = Block(
            blocking_user=self.user1,
        )
        serialized_block = BlockSerializer(block).data

        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
        ))

        request = APIRequestFactory().post(
            '/api/blocks',
            serialized_block,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
        ))
        return
    
    def test_delete_should_delete_block(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))

        request = APIRequestFactory().delete('/api/blocks/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request, pk=block.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Block.objects.filter(pk=block.pk))
        return

class MessageTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
        )
        self.user3.set_password("TestPassword3@98374")
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            timestamp=0,
            author=self.user1,
        )
        return
        
    def test_get_should_return_message_given_valid_sender(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_message = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_message, serialized_message)
        return
    
    def test_get_should_not_return_message_given_invalid_sender(self):
        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_messages)
        return
    
    def test_get_should_return_message_given_valid_receiver(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'receiver': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_message = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_message, serialized_message)
        return

    def test_get_should_not_return_message_given_invalid_receiver(self):
        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'receiver': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_messages)
        return
    
    def test_get_should_return_messages_given_valid_sender(self):
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            text="TestMessageTwo",
            timestamp=0,
        )
        message3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            text="TestMessageThree",
            timestamp=0,
        )
        serialized_message1 = MessageSerializer(message1).data
        serialized_message3 = MessageSerializer(message3).data
        serialized_messages = [serialized_message1, 
                                serialized_message3]

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_messages), len(serialized_messages))
        self.assertCountEqual(serialized_messages, response_messages)
        return

    def test_post_should_create_message_given_valid_message(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            text=message.text,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)
        response_message = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_message.get('receiver'), response_message.get('receiver'))
        self.assertEqual(response_message.get('sender'), response_message.get('sender'))
        self.assertEqual(response_message.get('text'), response_message.get('text'))
        self.assertTrue(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            text=message.text,
        ))
        return
    
    def test_post_should_not_create_message_given_invalid_message(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
        ))
        return
    
    def test_post_should_create_message_given_valid_message_with_embedded_post(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
            post=self.post1,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            text=message.text,
            post=self.post1,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)
        response_message = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_message.get('receiver'), response_message.get('receiver'))
        self.assertEqual(response_message.get('sender'), response_message.get('sender'))
        self.assertEqual(response_message.get('text'), response_message.get('text'))
        self.assertTrue(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            text=message.text,
            post=self.post1,
        ))
        return
    
    def test_post_should_not_message_given_sender_blocked_receiver(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data
        Block.objects.create(
            blocking_user=message.sender,
            blocked_user=message.receiver,
        )

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            text=message.text,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            text=message.text,
        ))
        return
    
    def test_post_should_not_message_given_receiver_blocked_sender(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data
        Block.objects.create(
            blocking_user=message.receiver,
            blocked_user=message.sender,
        )

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            text=message.text,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            text=message.text,
        ))
        return
    
    def test_delete_should_delete_message(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            text="TestMessageOne",
            timestamp=0,  
        )

        self.assertTrue(Message.objects.filter(pk=message.pk))

        request = APIRequestFactory().delete('/api/messages/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = MessageView.as_view({'delete':'destroy'})(request, pk=message.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Message.objects.filter(pk=message.pk))
        return

class WordTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        self.auth_token = Token.objects.create(user=self.user)

    def test_get_should_return_matching_words_given_partial_word(self):
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
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertFalse(word.get('text').find(word_to_search), -1)
        self.assertTrue(Word.objects.filter(text__contains=word_to_search))
        return
    
    def test_get_should_return_matching_words_given_full_word(self):
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
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertFalse(word.get('text').find(word_to_search), -1)
        self.assertTrue(Word.objects.filter(text__contains=word_to_search))
        return

class FriendRequestTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
        )
        self.user3.set_password("TestPassword3@98374")
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)
        return

    def test_get_should_return_friend_request_given_valid_friend_requesting_user(self):
        friend_request1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request2 = FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user3,
            timestamp=0,
        )
        serialized_friend_request1 = FriendRequestSerializer(friend_request1).data
        serialized_friend_request2 = FriendRequestSerializer(friend_request2).data
        
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requesting_user': friend_request1.friend_requesting_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_friend_request, serialized_friend_request1)
        return
    
    def test_get_should_not_return_friend_request_given_invalid_friend_requesting_user(self):
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requesting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_requests = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_friend_requests)
        return
    
    def test_get_should_return_friend_request_given_valid_friend_requested_user(self):
        friend_request1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request2 = FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user3,
            timestamp=0,
        )
        serialized_friend_request1 = FriendRequestSerializer(friend_request1).data
        serialized_friend_request2 = FriendRequestSerializer(friend_request2).data
        
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requested_user': friend_request1.friend_requested_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_friend_request, serialized_friend_request1)
        return
    
    def test_get_should_not_return_friend_request_given_invalid_friend_requested_user(self):
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requested_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_requests = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_friend_requests)
        return
    
    def test_post_should_create_friend_request_given_valid_friend_request(self):
        friend_request = FriendRequest(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        serialized_friend_request = FriendRequestSerializer(friend_request).data

        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
            friend_requested_user=friend_request.friend_requested_user,
        ))

        request = APIRequestFactory().post(
            '/api/friend_request/',
            serialized_friend_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'post':'create'})(request)
        response_friend_request = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_friend_request.get('friend_requesting_user'), 
                        serialized_friend_request.get('friend_requesting_user'))
        self.assertEqual(response_friend_request.get('friend_requested_user'), 
                        serialized_friend_request.get('friend_requested_user'))
        self.assertTrue(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
            friend_requested_user=friend_request.friend_requested_user,
        ))
        return
    
    def test_post_should_not_create_friend_request_given_invalid_friend_request(self):
        friend_request = FriendRequest(
            friend_requesting_user=self.user1,
        )
        serialized_friend_request = FriendRequestSerializer(friend_request).data

        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
        ))

        request = APIRequestFactory().post(
            '/api/friend_request/',
            serialized_friend_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
        ))
        return
    
    def test_delete_should_delete_friend_request(self):
        friend_request = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))

        request = APIRequestFactory().delete('/api/friend_request/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk=friend_request.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FriendRequest.objects.filter(pk=friend_request.pk))
        return

class FavoriteTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )
        return

    def test_get_should_return_favorites_given_favoriting_user(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        request = APIRequestFactory().get(
            '/api/favorites/',
            {
              'favoriting_user': self.user1.pk,  
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'get':'list'})(request)
        response_favorite = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_favorite, serialized_favorite)
        return

    def test_get_should_not_return_favorites_given_nonexistent_favoriting_user(self):
        request = APIRequestFactory().get(
            '/api/favorites/',
            {
              'favoriting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_post_should_create_favorite_given_valid_favorite(self):
        favorite = Favorite(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        self.assertFalse(Favorite.objects.filter(
            timestamp=favorite.timestamp,
            post=favorite.post,
            favoriting_user=favorite.favoriting_user,
        ))

        request = APIRequestFactory().post(
            '/api/favorites/',
            serialized_favorite,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'post':'create'})(request)
        response_favorite = response.data
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_favorite.get('post'),
                        serialized_favorite.get('post'))
        self.assertEqual(response_favorite.get('favoriting_user'),
                        serialized_favorite.get('favoriting_user'))
        self.assertTrue(Favorite.objects.filter(
            timestamp=favorite.timestamp,
            post=favorite.post,
            favoriting_user=favorite.favoriting_user,
        ))
        return
    
    def test_post_should_not_create_favorite_given_invalid_favorite(self):
        favorite = Favorite(
            timestamp=0,
            favoriting_user=self.user1
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        request = APIRequestFactory().post(
            '/api/favorites/',
            serialized_favorite,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_delete_should_delete_favorite(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )
        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))

        request = APIRequestFactory().delete('/api/favorite/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request, pk=favorite.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(pk=favorite.pk))
        return
    
class FeatureTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )
        return
    
    def test_get_should_return_all_features_given_no_parameters(self):
        feature = Feature.objects.create(
            timestamp=0,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return

    def test_get_should_return_features_with_timestamp_given_valid_timestamp(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'timestamp': feature.timestamp,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return
    
    def test_get_should_not_return_features_with_timestamp_given_invalid_timestamp(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'timestamp': feature.timestamp-1,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_get_should_return_features_with_post_given_valid_post(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'post': feature.post.pk,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return
    
    def test_get_should_not_return_features_with_timestamp_given_invalid_post(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'post': feature.post.pk-1,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

class MatchRequestTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
        )
        return
    
    def test_get_should_return_match_requests_given_valid_requesting_user(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        request = APIRequestFactory().get(
            '/api/match_requests',
            {
                'match_requesting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'get':'list'})(request)
        response_match_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_match_request, serialized_match_request)
        return
    
    def test_get_should_not_return_match_requests_given_invalid_requesting_user(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        request = APIRequestFactory().get(
            '/api/match_requests',
            {
                'match_requesting_user': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        return
    
    def test_post_should_create_match_request_given_valid_match_request(self):
        match_request = MatchRequest(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            match_requested_user=match_request.match_requested_user,
            post=self.post,
        ))

        request = APIRequestFactory().post(
            '/api/match_requests',
            serialized_match_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            match_requested_user=match_request.match_requested_user,
            post=self.post,
        ))
        return
    
    def test_post_should_not_create_match_request_given_invalid_match_request(self):
        match_request = MatchRequest(
            match_requesting_user=self.user1,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
        ))

        request = APIRequestFactory().post(
            '/api/match_requests',
            serialized_match_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
        ))
        return
    
    def test_delete_should_delete_match_request(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            '/api/match_requests',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request, pk=match_request.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MatchRequest.objects.filter(pk=match_request.pk))
        return


# ACCESSORY VIEWS

# Custom Relationship View Tests
class MatchViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
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

    def test_get_should_return_user1_given_user2(self):
        serialized_user1 = ReadOnlyUserSerializer(self.user1).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MatchView.as_view()(request)
        response_user1 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user1, serialized_user1)
        return

    def test_get_should_return_user2_given_user1(self):
        serialized_user2 = ReadOnlyUserSerializer(self.user2).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchView.as_view()(request)
        response_user2 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user2, serialized_user2)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
        )
        response = MatchView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class FriendshipViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user1,
            timestamp=0,
        )
        return

    def test_get_should_return_user1_given_user2(self):
        serialized_user1 = ReadOnlyUserSerializer(self.user1).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = FriendshipView.as_view()(request)
        response_user1 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user1, serialized_user1)
        return

    def test_get_should_return_user2_given_user1(self):
        serialized_user2 = ReadOnlyUserSerializer(self.user2).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendshipView.as_view()(request)
        response_user2 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user2, serialized_user2)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
        )
        response = FriendshipView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

# Custom Post View Tests
class MatchedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
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

    def test_get_should_not_return_matches_from_different_posts_given_no_parameters(self):
        return
    
    def test_get_should_return_only_bidirectional_matched_posts_given_no_paramters(self):
        return

class FeaturedPostsViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
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
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
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
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            text='FakeTextForFirstPost',
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