import os
from unittest import skipIf
from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from freezegun import freeze_time
from unittest.mock import patch

from mist_worker.tasks import send_mistbox_notifications, tally_random_upvotes, verify_profile_picture
from mist.models import Post, PostVote
from push_notifications.models import APNSDevice
from users.tests.generics import create_dummy_user_and_token_given_id, create_simple_uploaded_file_from_image_path

# Create your tests here.

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message):
        NotificationServiceMock.sent_notifications.append(message)

@patch('push_notifications.models.APNSDeviceQuerySet.send_message', 
    NotificationServiceMock.send_fake_notification)
class TasksTest(TestCase):
    def setUp(self):
        NotificationServiceMock.sent_notifications = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

        self.user1.keywords = ["hello", "these", "are", "my", "keywords"]
        self.user2.keywords = ["hello", "these", "are", "my", "keywords"]

        self.user1.save()
        self.user2.save()

        self.post1 = Post.objects.create(
            title=self.user1.keywords[0],
            body=self.user1.keywords[1],
            author=self.user2,
        )
        self.post2 = Post.objects.create(
            title=self.user1.keywords[2],
            body=self.user2.keywords[0],
            author=self.user3,

        )
        self.post3 = Post.objects.create(
            title=self.user2.keywords[0],
            body=self.user2.keywords[1],
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
    
    # def test_make_daily_mistboxes(self):
    #     make_daily_mistboxes()
    #     mistbox1 = Mistbox.objects.filter(user=self.user1)[0]
    #     mistbox2 = Mistbox.objects.filter(user=self.user2)[0]
    #     mistboxposts1 = Post.objects.filter(mistboxes=mistbox1)
    #     mistboxposts2 = Post.objects.filter(mistboxes=mistbox2)
    #     self.assertTrue(mistbox1)
    #     self.assertTrue(mistbox2)
    #     self.assertTrue(mistboxposts1)
    #     self.assertTrue(mistboxposts2)

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

        verify_profile_picture(self.user1)
        verify_profile_picture(self.user2)

        self.assertFalse(self.user1.is_pending_verification)
        self.assertFalse(self.user2.is_pending_verification)
