from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIRequestFactory

from mist.models import Post, View
from mist.views.view import ViewPost
from users.tests.generics import create_dummy_user_and_token_given_id

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message, *args, **kwargs):
        NotificationServiceMock.sent_notifications.append(message)

@freeze_time("2020-01-01")
class ViewTest(TestCase):
    def setUp(self):
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

    def test_post_should_create_view_given_valid_posts(self):
        request = APIRequestFactory().post(
            '/api/views',
            {
                'posts': [self.post1.id, self.post2.id, self.post3.id],
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ViewPost.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(View.objects.filter(post=self.post1, user=self.user1))
        self.assertTrue(View.objects.filter(post=self.post2, user=self.user1))
        self.assertTrue(View.objects.filter(post=self.post3, user=self.user1))
        return

    def test_post_should_create_views_for_valid_posts_given_valid_and_invalid_posts(self):
        nonexistent_pk = -1
        request = APIRequestFactory().post(
            '/api/views',
            {
                'posts': [self.post1.id, self.post2.id, nonexistent_pk],
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ViewPost.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(View.objects.filter(post=self.post1, user=self.user1))
        self.assertTrue(View.objects.filter(post=self.post2, user=self.user1))
        self.assertFalse(View.objects.filter(post=self.post3, user=self.user1))
        return