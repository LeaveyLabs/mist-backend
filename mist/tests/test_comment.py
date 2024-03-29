from datetime import date
from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIRequestFactory
from mist.models import Comment, CommentFlag, Post, Tag
from mist.serializers import CommentSerializer, TagSerializer
from mist.views.comment import CommentView

from users.models import User
from users.serializers import ReadOnlyUserSerializer
from users.tests.generics import create_dummy_user_and_token_given_id

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message, *args, **kwargs):
        NotificationServiceMock.sent_notifications.append(message)


@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message', 
    NotificationServiceMock.send_fake_notification)
class CommentTest(TestCase):
    maxDiff = None

    def setUp(self):
        NotificationServiceMock.sent_notifications = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

        self.read_only_user1 = ReadOnlyUserSerializer(self.user1)
        self.read_only_user2 = ReadOnlyUserSerializer(self.user2)
        self.read_only_user3 = ReadOnlyUserSerializer(self.user3)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )

        self.comment1 = Comment.objects.create(
            body='FakeTextForComment',
            post=self.post,
            author=self.user1,
            timestamp=0,
        )

        self.unused_post_id = 155
        return
        
    def test_get_should_return_comment_given_post_pk(self):
        serialized_comment = CommentSerializer(self.comment1).data

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_comment, response_comment)
        self.assertIn('author', response_comment)
        self.assertIn('read_only_author', response_comment)
        self.assertIn('votecount', response_comment)
        self.assertIn('flagcount', response_comment)
        self.assertEqual(self.read_only_user1.data, response_comment.get('read_only_author'))
        return
    
    def test_get_should_return_comment_with_tags(self):
        tag = Tag.objects.create(comment=self.comment1, tagging_user=self.user1, tagged_user=self.user2)
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_comment.get('tags'), [serialized_tag])
        return
    
    def test_get_should_not_return_comment_given_invalid_post_pk(self):
        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.unused_post_id,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comments = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_comments)
        return
    
    
    def test_get_should_not_return_comments_with_excessive_flags(self):
        CommentFlag.objects.create(flagger=self.user1, comment=self.comment1)
        CommentFlag.objects.create(flagger=self.user2, comment=self.comment1)
        CommentFlag.objects.create(flagger=self.user3, comment=self.comment1)

        serialized_comment = CommentSerializer(self.comment1).data

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comments = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(serialized_comment not in response_comments)
        return
    
    def test_get_should_not_return_comments_with_superuser_flags(self):
        superuser = User.objects.create(
            email="superuser@usc.edu",
            username="superuser",
            date_of_birth=date(2000, 1, 1),
            is_superuser=True,
        )
        serialized_comment = CommentSerializer(self.comment1).data
        CommentFlag.objects.create(flagger=superuser, comment=self.comment1)

        request = APIRequestFactory().get(
            '/api/comments',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )

        response = CommentView.as_view({'get':'list'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(serialized_comment not in response.data)
        return

    def test_get_should_return_comments_in_time_order(self):
        comment2 = Comment.objects.create(
            body='FakeTextForComment',
            post=self.post,
            author=self.user2,
            timestamp=self.comment1.timestamp+1,
        )

        serialized_comment1 = CommentSerializer(self.comment1).data
        serialized_comment2 = CommentSerializer(comment2).data
        serialized_ordered_comments = [serialized_comment1, serialized_comment2]

        request = APIRequestFactory().get(
            '/api/comments',
            {
                'post': self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comments = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_comments, serialized_ordered_comments)
        return

    def test_post_should_create_comment_given_valid_comment(self):
        test_comment = Comment(
            body='FakeTextForTestComment',
            post=self.post,
            author=self.user1
        )
        serialized_comment = CommentSerializer(test_comment).data

        self.assertFalse(Comment.objects.filter(
            body=test_comment.body,
            post=test_comment.post,
            author=test_comment.author))

        request = APIRequestFactory().post(
            '/api/comments/',
            serialized_comment,
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'post':'create'})(request)
        response_comment = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_comment.get('body'), serialized_comment.get('body'))
        self.assertEqual(response_comment.get('post'), serialized_comment.get('post'))
        self.assertEqual(response_comment.get('author'), serialized_comment.get('author'))
        self.assertTrue(Comment.objects.filter(
            body=test_comment.body,
            post=test_comment.post,
            author=test_comment.author))
        return

    def test_post_should_send_notification_given_valid_comment(self):
        test_comment = Comment(
            body='FakeTextForTestComment',
            post=self.post,
            author=self.user1
        )
        serialized_comment = CommentSerializer(test_comment).data

        request = APIRequestFactory().post(
            '/api/comments/',
            serialized_comment,
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NotificationServiceMock.sent_notifications)
        return
    
    def test_post_should_not_send_notification_given_valid_comment(self):
        non_existent_user_id = -1

        test_comment = Comment(
            body='FakeTextForTestComment',
            post=self.post,
            author=self.user1
        )
        serialized_comment = CommentSerializer(test_comment).data
        serialized_comment['author'] = non_existent_user_id

        request = APIRequestFactory().post(
            '/api/comments/',
            serialized_comment,
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'post':'create'})(request)

        self.assertFalse(NotificationServiceMock.sent_notifications)
        return
    
    # def test_post_should_not_create_given_profanity(self):
    #     test_comment = Comment(
    #         body='fuck shit ass',
    #         post=self.post,
    #         author=self.user1
    #     )
    #     serialized_comment = CommentSerializer(test_comment).data

    #     request = APIRequestFactory().post(
    #         '/api/comments/',
    #         serialized_comment,
    #         format="json",
    #         HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
    #     )
    #     response = CommentView.as_view({'post':'create'})(request)

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertFalse(Comment.objects.filter(
    #         body=test_comment.body))
    #     return

    # def test_post_should_not_create_given_hate_speech(self):
    #     test_comment = Comment(
    #         body='nigger nigga',
    #         post=self.post,
    #         author=self.user1
    #     )
    #     serialized_comment = CommentSerializer(test_comment).data

    #     request = APIRequestFactory().post(
    #         '/api/comments/',
    #         serialized_comment,
    #         format="json",
    #         HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
    #     )
    #     response = CommentView.as_view({'post':'create'})(request)

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertFalse(Comment.objects.filter(
    #         body=test_comment.body))
    #     return

    def test_delete_should_delete_comment(self):
        self.assertTrue(Comment.objects.filter(pk=self.comment1.pk))

        request = APIRequestFactory().delete('/api/comment/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = CommentView.as_view({'delete':'destroy'})(request, pk=self.comment1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment1.pk))
        return