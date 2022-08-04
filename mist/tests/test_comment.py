from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, CommentFlag, Post, Tag
from mist.serializers import CommentSerializer, TagSerializer
from mist.views.comment import CommentView

from users.models import User
from users.serializers import ReadOnlyUserSerializer

class CommentTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            first_name='Test',
            last_name='User',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword@98374")
        self.user1.save()
        self.read_only_user1 = ReadOnlyUserSerializer(self.user1)
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            first_name='Test',
            last_name='User',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword@98374")
        self.user2.save()
        self.read_only_user2 = ReadOnlyUserSerializer(self.user2)
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
            first_name='Test',
            last_name='User',
            date_of_birth=date(2000, 1, 1),
        )
        self.user3.set_password("TestPassword@98374")
        self.user3.save()
        self.read_only_user3 = ReadOnlyUserSerializer(self.user3)
        self.auth_token3 = Token.objects.create(user=self.user3)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )

        self.comment = Comment.objects.create(
            body='FakeTextForComment',
            post=self.post,
            author=self.user1,
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentView.as_view({'get':'list'})(request)
        response_comment = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_comment, response_comment)
        self.assertIn('author', response_comment)
        self.assertIn('read_only_author', response_comment)
        self.assertEqual(self.read_only_user1.data, response_comment.get('read_only_author'))
        return
    
    def test_get_should_return_comment_with_tags(self):
        tag = Tag.objects.create(comment=self.comment, tagging_user=self.user1, tagged_user=self.user2)
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
        CommentFlag.objects.create(flagger=self.user1, comment=self.comment)
        CommentFlag.objects.create(flagger=self.user2, comment=self.comment)
        CommentFlag.objects.create(flagger=self.user3, comment=self.comment)

        serialized_comment = CommentSerializer(self.comment).data

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

    def test_delete_should_delete_comment(self):
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk))

        request = APIRequestFactory().delete('/api/comment/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = CommentView.as_view({'delete':'destroy'})(request, pk=self.comment.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk))
        return