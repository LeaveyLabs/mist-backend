from datetime import date
from unittest.mock import patch
from push_notifications.models import APNSDevice
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Block, MatchRequest, Message, Post
from mist.serializers import MessageSerializer
from mist.views.message import ConversationView, MessageView

from users.models import User

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message):
        NotificationServiceMock.sent_notifications.append(message)

@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message', 
    NotificationServiceMock.send_fake_notification)
class MessageTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)
        APNSDevice.objects.create(
            user=self.user1,
            registration_id="randomRegistrationId1"
        )

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)
        APNSDevice.objects.create(
            user=self.user2,
            registration_id="randomRegistrationId2"
        )

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
            date_of_birth=date(2000, 1, 1),
        )
        self.user3.set_password("TestPassword3@98374")
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)
        APNSDevice.objects.create(
            user=self.user3,
            registration_id="randomRegistrationId3"
        )

        self.post1 = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            timestamp=0,
            author=self.user1,
        )
        return
        
    def test_get_should_return_message_given_valid_sender(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_message = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_message, serialized_message)
        return
    
    def test_get_should_not_return_message_given_invalid_sender(self):
        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_messages)
        return
    
    def test_get_should_return_message_given_valid_receiver(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'receiver': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_message = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_message, serialized_message)
        return

    def test_get_should_not_return_message_given_invalid_receiver(self):
        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'receiver': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_messages)
        return
    
    def test_get_should_return_messages_given_valid_sender(self):
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            body="TestMessageTwo",
            timestamp=0,
        )
        message3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            body="TestMessageThree",
            timestamp=0,
        )
        serialized_message1 = MessageSerializer(message1).data
        serialized_message3 = MessageSerializer(message3).data
        serialized_messages = [serialized_message1, 
                                serialized_message3]

        request = APIRequestFactory().get(
            '/api/messages/',
            {
                'sender': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'get':'list'})(request)
        response_messages = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_messages), len(serialized_messages))
        self.assertCountEqual(serialized_messages, response_messages)
        return

    def test_post_should_create_message_given_valid_message(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            body=message.body,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)
        response_message = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_message.get('receiver'), response_message.get('receiver'))
        self.assertEqual(response_message.get('sender'), response_message.get('sender'))
        self.assertEqual(response_message.get('body'), response_message.get('body'))
        self.assertTrue(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            body=message.body,
        ))
        return

    def test_post_should_send_notification_with_username_given_message_to_matched_user(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
        )
        MatchRequest.objects.create(
            match_requesting_user=self.user2,
            match_requested_user=self.user1,
        )

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(
            f"{message.sender.username}: {message.body}",
            NotificationServiceMock.sent_notifications)
        return

    def test_post_should_send_anonymous_notification_given_message_to_unmatched_user(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(
            f"Someone sent you a special message ❤️", 
            NotificationServiceMock.sent_notifications)
        return
    
    def test_post_should_not_create_message_given_invalid_message(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
        ))
        return
    
    def test_post_should_create_message_given_valid_message_with_embedded_post(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
            post=self.post1,
        )
        serialized_message = MessageSerializer(message).data

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            body=message.body,
            post=self.post1,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)
        response_message = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_message.get('receiver'), response_message.get('receiver'))
        self.assertEqual(response_message.get('sender'), response_message.get('sender'))
        self.assertEqual(response_message.get('body'), response_message.get('body'))
        self.assertTrue(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            body=message.body,
            post=self.post1,
        ))
        return
    
    def test_post_should_not_message_given_sender_blocked_receiver(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data
        Block.objects.create(
            blocking_user=message.sender,
            blocked_user=message.receiver,
        )

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            body=message.body,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            body=message.body,
        ))
        return
    
    def test_post_should_not_message_given_receiver_blocked_sender(self):
        message = Message(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,
        )
        serialized_message = MessageSerializer(message).data
        Block.objects.create(
            blocking_user=message.receiver,
            blocked_user=message.sender,
        )

        self.assertFalse(Message.objects.filter(
            sender=message.sender,
            receiver=message.receiver,
            body=message.body,
        ))

        request = APIRequestFactory().post(
            '/api/messages/',
            serialized_message,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MessageView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Message.objects.filter(
            sender=self.user1,
            receiver=self.user2,
            body=message.body,
        ))
        return
    
    def test_delete_should_delete_message(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            body="TestMessageOne",
            timestamp=0,  
        )

        self.assertTrue(Message.objects.filter(pk=message.pk))

        request = APIRequestFactory().delete('/api/messages/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = MessageView.as_view({'delete':'destroy'})(request, pk=message.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Message.objects.filter(pk=message.pk))
        return

@freeze_time('2022-06-26')
class ConversationViewTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User(
            email='TestUser3@usc.edu',
            username='TestUser3',
            date_of_birth=date(2000, 1, 1),
        )
        self.user3.set_password("TestPassword3@98374")
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)
        return
    
    def test_get_should_return_status_error_given_invalid_token(self):
        request = APIRequestFactory().get(
            'api/conversations', 
            HTTP_AUTHORIZATION=f'Token INVALIDTOKEN')
        response = ConversationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_should_return_all_user_conversations_given_no_parameters(self):
        user1_to_user2 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            body='TestMessageBody1'
        )
        user1_to_user3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            body='TestMessageBody2'
        )
        user2_to_user1 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            body='TestMessageBody3'
        )
        user2_to_user3 = Message.objects.create(
            sender=self.user2,
            receiver=self.user3,
            body='TestMessageBody4'
        )
        user3_to_user2 = Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            body='TestMessageBody5'
        )
        user3_to_user1 = Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            body='TestMessageBody6'
        )
        expected_response_data = {
            self.user2.pk: [
                MessageSerializer(user1_to_user2).data,
                MessageSerializer(user2_to_user1).data,
            ],
            self.user3.pk: [
                MessageSerializer(user1_to_user3).data,
                MessageSerializer(user3_to_user1).data,
            ]
        }

        request = APIRequestFactory().get(
            'api/conversations', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = ConversationView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get(self.user2.pk), expected_response_data.get(self.user2.pk))
        self.assertEqual(response.data.get(self.user3.pk), expected_response_data.get(self.user3.pk))
        return