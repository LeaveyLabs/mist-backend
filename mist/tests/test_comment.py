from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, Post
from mist.serializers import CommentSerializer
from mist.views.comment import CommentView

from users.models import User
from users.serializers import ReadOnlyUserSerializer

class CommentTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
            first_name='Test',
            last_name='User',
            date_of_birth=date(2000, 1, 1),
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        self.read_only_user = ReadOnlyUserSerializer(self.user)
        self.auth_token = Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user,
        )

        self.comment = Comment.objects.create(
            body='FakeTextForComment',
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
                'post': self.post.pk,
            },
            format="json",
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_comment, response_comment)
        self.assertIn('author', response_comment)
        self.assertIn('read_only_author', response_comment)
        self.assertEqual(self.read_only_user.data, response_comment.get('read_only_author'))
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
        self.assertNotIn('author', response_comment)
        self.assertNotIn('read_only_author', response_comment)
        return

    def test_post_should_create_comment_given_valid_comment(self):
        test_comment = Comment(
            body='FakeTextForTestComment',
            post=self.post,
            author=self.user
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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

    def test_delete_should_delete_comment(self):
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk))

        request = APIRequestFactory().delete('/api/comment/', HTTP_AUTHORIZATION=f'Token {self.auth_token}')
        response = CommentView.as_view({'delete':'destroy'})(request, pk=self.comment.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk))
        return