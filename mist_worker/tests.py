from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from freezegun import freeze_time
from unittest.mock import patch

from mist_worker.tasks import make_daily_mistboxes, send_mistbox_notifications, tally_random_upvotes
from mist.models import Mistbox, MistboxPost, Post, PostVote
from push_notifications.models import APNSDevice
from users.tests.generics import create_dummy_user_and_token_given_id

# Create your tests here.

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message):
        NotificationServiceMock.sent_notifications.append(message)

@freeze_time("2020-01-01")
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

    def test_send_mistbox_notifications(self):
        send_mistbox_notifications()
        self.assertTrue(NotificationServiceMock.sent_notifications)
        for notification in NotificationServiceMock.sent_notifications:
            self.assertTrue('mistbox' in notification)
    
    def test_make_daily_mistboxes(self):
        make_daily_mistboxes()
        mistbox1 = Mistbox.objects.filter(user=self.user1)[0]
        mistbox2 = Mistbox.objects.filter(user=self.user2)[0]
        mistboxposts1 = MistboxPost.objects.filter(mistbox_id=mistbox1)
        mistboxposts2 = MistboxPost.objects.filter(mistbox_id=mistbox2)
        self.assertTrue(mistbox1)
        self.assertTrue(mistbox2)
        self.assertTrue(mistboxposts1)
        self.assertTrue(mistboxposts2)

    def test_tally_random_upvotes(self):
        tally_random_upvotes()
        post_votes_1 = PostVote.objects.filter(post=self.post1)
        post_votes_2 = PostVote.objects.filter(post=self.post2)
        post_votes_3 = PostVote.objects.filter(post=self.post3)
        self.assertTrue(
            post_votes_1 or post_votes_2 or post_votes_3)
