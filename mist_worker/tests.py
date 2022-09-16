import os
from unittest import skipIf
from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from unittest.mock import patch

from mist_worker.tasks import reset_mistbox_opens, send_make_your_day_mist_notifications, send_mistbox_notifications, tally_random_upvotes, verify_profile_picture
from mist.models import Mistbox, Post, PostVote
from push_notifications.models import APNSDevice
from users.tests.generics import create_dummy_user_and_token_given_id, create_simple_uploaded_file_from_image_path

# Create your tests here.

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message, extra):
        NotificationServiceMock.sent_notifications.append(message)

@patch('push_notifications.models.APNSDeviceQuerySet.send_message', 
    NotificationServiceMock.send_fake_notification)
class TasksTest(TestCase):
    def setUp(self):
        NotificationServiceMock.sent_notifications = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

        keywords = ["these", "are", "test", "keywords"]

        self.post1 = Post.objects.create(
            title=keywords[0],
            body=keywords[1],
            author=self.user2,
        )
        self.post2 = Post.objects.create(
            title=keywords[2],
            body=keywords[0],
            author=self.user3,

        )
        self.post3 = Post.objects.create(
            title=keywords[0],
            body=keywords[1],
            author=self.user1,
        )

        APNSDevice.objects.create(user=self.user1, registration_id='1')
        APNSDevice.objects.create(user=self.user1, registration_id='2')

        self.obama_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/obama1.jpeg', 
            'obama1.jpeg')
        self.obama_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/obama2.jpeg', 
            'obama2.jpeg')
        self.kevin_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/kevin1.jpeg', 
            'kevin1.jpeg')
        self.kevin_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/kevin2.jpeg', 
            'kevin2.jpeg')
        self.adam_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/adam1.jpeg', 
            'adam1.jpeg')
        self.adam_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/adam2.jpeg', 
            'adam2.jpeg')

    def test_send_mistbox_notifications(self):
        send_mistbox_notifications()
        self.assertTrue(NotificationServiceMock.sent_notifications)
        for notification in NotificationServiceMock.sent_notifications:
            self.assertIn('mistbox', notification)

    def test_reset_mistbox_swipecount(self):
        for mistbox in Mistbox.objects.all():
            mistbox.opens_used_today = 10
            mistbox.save()
        
        reset_mistbox_opens()

        for mistbox in Mistbox.objects.all():
            self.assertEqual(mistbox.opens_used_today, 0)

    def test_tally_random_upvotes(self):
        tally_random_upvotes()
        post_votes_1 = PostVote.objects.filter(post=self.post1)
        post_votes_2 = PostVote.objects.filter(post=self.post2)
        post_votes_3 = PostVote.objects.filter(post=self.post3)
        self.assertTrue(
            post_votes_1 or post_votes_2 or post_votes_3)

    @skipIf(int(os.environ.get("SKIP_SLOW_TESTS", 0)), "slow")
    def test_verify_profile_picture(self):
        self.user1.picture = self.kevin_image_file1
        self.user1.confirm_picture = self.kevin_image_file2
        self.user1.save()

        self.user2.picture = self.obama_image_file1
        self.user2.confirm_picture = self.kevin_image_file2
        self.user2.save()

        verify_profile_picture(self.user1.id)
        verify_profile_picture(self.user2.id)

        self.assertFalse(self.user1.is_pending_verification)
        self.assertFalse(self.user2.is_pending_verification)

    def test_send_write_mist_notifications(self):
        send_make_your_day_mist_notifications()
        self.assertTrue(NotificationServiceMock.sent_notifications)
        for notification in NotificationServiceMock.sent_notifications:
            self.assertIn('mist', notification)
