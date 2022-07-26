from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, CommentFlag, Post
from mist.serializers import CommentFlagSerializer
from mist.views.comment_flag import CommentFlagView

from users.models import User

class CommentFlagTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
            date_of_birth=date(2000, 1, 1),
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        self.auth_token = Token.objects.create(user=self.user)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user,
        )
        self.comment = Comment.objects.create(
            body="FakeTextForFirstComment",
            author=self.user,
            post=self.post,
        )
        return

    def test_get_should_return_flag_given_valid_flagger(self):
        flag = CommentFlag.objects.create(
            flagger=self.user,
            comment=self.comment,
            timestamp=0,
        )
        serialized_flag = CommentFlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'flagger': flag.flagger.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentFlagView.as_view({'get':'list'})(request)
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
        response = CommentFlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_get_should_return_flag_given_valid_comment(self):
        flag = CommentFlag.objects.create(
            flagger=self.user,
            comment=self.comment,
            timestamp=0,
        )
        serialized_flag = CommentFlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'post': flag.comment.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentFlagView.as_view({'get':'list'})(request)
        response_flag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_flag, serialized_flag)
        return
    
    def test_get_should_not_return_flag_given_invalid_comment(self):
        request = APIRequestFactory().get(
            '/api/flags',
            {
                'post': self.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentFlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_post_should_create_flag_given_valid_flag(self):
        flag = CommentFlag(
            flagger=self.user,
            comment=self.comment,
            timestamp=0,
        )
        serialized_flag = CommentFlagSerializer(flag).data

        self.assertFalse(CommentFlag.objects.filter(
            flagger=flag.flagger,
            comment=flag.comment,
            timestamp=flag.timestamp,
        ))

        request = APIRequestFactory().post(
            '/api/flags/',
            serialized_flag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = CommentFlagView.as_view({'post':'create'})(request)
        response_flag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_flag.get('flagger'), serialized_flag.get('flagger'))
        self.assertEqual(response_flag.get('post'), serialized_flag.get('post'))
        self.assertTrue(CommentFlag.objects.filter(
            flagger=flag.flagger,
            comment=flag.comment,
            timestamp=flag.timestamp,
        ))
        return
    
    def test_delete_should_delete_flag(self):
        flag = CommentFlag.objects.create(
            flagger=self.user,
            comment=self.comment,
        )
        self.assertTrue(CommentFlag.objects.filter(pk=flag.pk))
        request = APIRequestFactory().delete('/api/flags/', HTTP_AUTHORIZATION=f'Token {self.auth_token}')
        response = CommentFlagView.as_view({'delete':'destroy'})(request, pk=flag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CommentFlag.objects.filter(pk=flag.pk))
        return