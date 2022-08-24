from datetime import date
import os
from unittest import skipIf
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import PostFlag, Post
from mist.serializers import PostFlagSerializer
from mist.views.post_flag import PostFlagView

from users.models import Ban, User

@freeze_time("2020-01-01")
class PostFlagTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 =  User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )
        return

    def test_get_should_return_flag_given_valid_flagger(self):
        flag = PostFlag.objects.create(
            flagger=self.user1,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = PostFlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'flagger': flag.flagger.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostFlagView.as_view({'get':'list'})(request)
        response_flag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_flag, serialized_flag)
        return
    
    def test_get_should_not_return_flag_given_invalid_flagger(self):
        request = APIRequestFactory().get(
            '/api/flags',
            {
                'flagger': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostFlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_get_should_return_flag_given_valid_post(self):
        flag = PostFlag.objects.create(
            flagger=self.user1,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = PostFlagSerializer(flag).data

        request = APIRequestFactory().get(
            '/api/flags',
            {
                'post': flag.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostFlagView.as_view({'get':'list'})(request)
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostFlagView.as_view({'get':'list'})(request)
        response_flags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_flags)
        return
    
    def test_post_should_create_flag_given_valid_flag(self):
        flag = PostFlag(
            flagger=self.user1,
            post=self.post,
            timestamp=0,
        )
        serialized_flag = PostFlagSerializer(flag).data

        self.assertFalse(PostFlag.objects.filter(
            flagger=flag.flagger,
            post=flag.post,
            timestamp=flag.timestamp,
        ))

        request = APIRequestFactory().post(
            '/api/flags/',
            serialized_flag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostFlagView.as_view({'post':'create'})(request)
        response_flag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_flag.get('flagger'), serialized_flag.get('flagger'))
        self.assertEqual(response_flag.get('post'), serialized_flag.get('post'))
        self.assertTrue(PostFlag.objects.filter(
            flagger=flag.flagger,
            post=flag.post,
            timestamp=flag.timestamp,
        ))
        return
    
    @skipIf(int(os.environ.get("SKIP_SLOW_TESTS", 0)), "slow")
    def test_post_should_ban_user_given_many_impermissble_posts(self):

        MANY_IMPERMISSIBLE_POSTS = 11
        MANY_FLAGS = 11
        
        # Generalized functions
        def create_dummy_user_with_token(id):
            username_handle = f'testUser{id}'
            user = User.objects.create(
                email=f'{username_handle}@usc.edu',
                username=username_handle,
                date_of_birth=date(2000, 1, 1),
            )
            token = Token.objects.create(
                user=user
            )
            return (user, token)

        def post_flag(post, user, token):
            flag = PostFlag(
                post=post,
                flagger=user,
            )
            serialized_flag = PostFlagSerializer(flag).data
            request = APIRequestFactory().post(
                '/api/flags/',
                serialized_flag,
                format='json',
                HTTP_AUTHORIZATION=f'Token {token}',
            )
            PostFlagView.as_view({'post':'create'})(request)

        def post_flags_to_many_impermissible_posts():
            for _ in range(MANY_IMPERMISSIBLE_POSTS):
                impermissible_post = Post.objects.create(
                    title='impermissible post', 
                    body='impermissible post',
                    author=self.user1)
                for (user, token) in test_users:
                    post_flag(impermissible_post, user, token)

        # Configured test
        test_users = [create_dummy_user_with_token(i) for i in range(MANY_FLAGS)]

        self.assertTrue(User.objects.filter(id=self.user1.id))
        self.assertFalse(Ban.objects.filter(email=self.user1.email))

        post_flags_to_many_impermissible_posts()

        self.assertFalse(User.objects.filter(id=self.user1.id))
        self.assertTrue(Ban.objects.filter(email=self.user1.email))
    
    def test_delete_should_delete_flag(self):
        flag = PostFlag.objects.create(
            flagger=self.user1,
            post=self.post,
        )
        self.assertTrue(PostFlag.objects.filter(pk=flag.pk))
        request = APIRequestFactory().delete('/api/flags/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = PostFlagView.as_view({'delete':'destroy'})(request, pk=flag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostFlag.objects.filter(pk=flag.pk))
        return