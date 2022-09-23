from datetime import date, datetime, timedelta
from unittest.mock import patch
from django.core import mail, cache
from django.test import TestCase
from freezegun import freeze_time
from users.generics import get_current_time
from users.models import Notification, User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.tests.generics import NotificationServiceMock
from users.serializers import OpenedNotificationSerializer
from users.tests.generics import create_dummy_user_and_token_given_id
from users.views.notifications import OpenedNotificationView

from users.views.register import RegisterPhoneNumberView, RegisterUserEmailView, ValidatePhoneNumberView, ValidateUserEmailView, ValidateUsernameView
from users.models import Ban, EmailAuthentication, PhoneNumberAuthentication, User

import sys
sys.path.append("..")
from twilio_config import TwillioTestClientMessages

@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class NotificationsTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

    def test_save_should_send_apns_notification_with_correct_badge_count(self):
        NotificationServiceMock.sent_notifications = []
        NotificationServiceMock.badges = 0

        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.MESSAGE,
            sangdaebang=self.user2,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 1)
    
@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class OpenedNotificationsViewTest(TestCase):
    def setUp(self):
        NotificationServiceMock.badges = 0

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

    def test_post_should_update_badges_correctly_given_nonmessage_notification(self):
        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 2)

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'type': Notification.NotificationTypes.COMMENT,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenedNotificationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NotificationServiceMock.badges, 0)

    def test_post_should_updage_badges_correctly_given_message_notification(self):
        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        Notification.objects.create(
            user=self.user1,
            sangdaebang=self.user2,
            type=Notification.NotificationTypes.MESSAGE,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 3)

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'sangdaebang': self.user2.id,
                'type': Notification.NotificationTypes.MESSAGE,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenedNotificationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NotificationServiceMock.badges, 2)

    def test_post_should_not_update_badges_given_invalid_notification_type(self):
        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'type': 'invalid_type',
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenedNotificationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(NotificationServiceMock.badges, 2)

    def test_post_should_not_update_badges_given_no_timestamp(self):
        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        Notification.objects.create(
            user=self.user1,
            type=Notification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'type': 'invalid_type',
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenedNotificationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(NotificationServiceMock.badges, 2)