from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from users.generics import get_current_time
from users.models import UserNotification, User
from rest_framework import status
from rest_framework.test import APIRequestFactory
from mist.tests.generics import NotificationServiceMock
from users.tests.generics import create_dummy_user_and_token_given_id
from users.views.notifications import LastOpenedNotificationTime, OpenNotifications

@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class NotificationsTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

    def test_save_should_send_apns_notification_with_correct_badgecount(self):
        NotificationServiceMock.sent_notifications = []
        NotificationServiceMock.badges = 0

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.MESSAGE,
            sangdaebang=self.user2,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 1)

    def test_save_should_exclude_automated_notifications_in_badgecount(self):
        NotificationServiceMock.sent_notifications = []
        NotificationServiceMock.badges = 0

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.PROMPTS,
        )

        self.assertEqual(NotificationServiceMock.badges, 0)
    
@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class OpenedNotificationsViewTest(TestCase):
    def setUp(self):
        NotificationServiceMock.badges = 0

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

    def test_post_should_enable_badges_given_notification(self):
        self.user1.notification_badges_enabled = False
        self.user1.save()

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'type': UserNotification.NotificationTypes.COMMENT,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenNotifications.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(id=self.user1.id).notification_badges_enabled)

    def test_post_should_update_badges_correctly_given_nonmessage_notification(self):
        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 2)

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'type': UserNotification.NotificationTypes.COMMENT,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenNotifications.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NotificationServiceMock.badges, 0)

    def test_post_should_updage_badges_correctly_given_message_notification(self):
        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        UserNotification.objects.create(
            user=self.user1,
            sangdaebang=self.user2,
            type=UserNotification.NotificationTypes.MESSAGE,
            message='this is a test',
        )

        self.assertEqual(NotificationServiceMock.badges, 3)

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'timestamp': get_current_time(),
                'sangdaebang': self.user2.id,
                'type': UserNotification.NotificationTypes.MESSAGE,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenNotifications.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(NotificationServiceMock.badges, 2)

    def test_post_should_not_update_badges_given_invalid_notification_type(self):
        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
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
        response = OpenNotifications.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(NotificationServiceMock.badges, 2)

    def test_post_should_not_update_badges_given_no_timestamp(self):
        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
        )

        request = APIRequestFactory().post(
            'api/open-notification/',
            {
                'type': 'invalid_type',
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = OpenNotifications.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(NotificationServiceMock.badges, 2)

@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message',
    NotificationServiceMock.send_fake_notification)
class LastOpenedNotificationViewTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
    
    def test_get_should_return_last_open_time_given_message_notification_type_and_sangaebang(self):
        notification = UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.MESSAGE,
            sangdaebang=self.user2,
            message='this is a test',
            has_been_seen=True,
        )

        request = APIRequestFactory().get(
            f'api/last-opened-time/?type={UserNotification.NotificationTypes.MESSAGE}&sangdaebang={self.user2.id}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = LastOpenedNotificationTime.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(notification.timestamp, response.data.get('timestamp'))

    def test_get_should_return_zero_given_never_opened_notifications(self):
        request = APIRequestFactory().get(
            f'api/last-opened-time/?type={UserNotification.NotificationTypes.MESSAGE}&sangdaebang={self.user2.id}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = LastOpenedNotificationTime.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, response.data.get('timestamp'))

    def test_get_should_return_last_opened_notification_given_nonmessage_notification_type(self):
        notification = UserNotification.objects.create(
            user=self.user1,
            type=UserNotification.NotificationTypes.COMMENT,
            message='this is a test',
            has_been_seen=True,
        )

        request = APIRequestFactory().get(
            f'api/last-opened-time/?type={UserNotification.NotificationTypes.COMMENT}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = LastOpenedNotificationTime.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(notification.timestamp, response.data.get('timestamp'))

    def test_get_should_return_zero_given_unseen_notification_type(self):
        request = APIRequestFactory().get(
            'api/last-opened-time/?type=invalid_type',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = LastOpenedNotificationTime.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, response.data.get('timestamp'))