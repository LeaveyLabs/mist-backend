from datetime import date
from unittest.mock import patch
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import MatchRequest, Post
from mist.serializers import MatchRequestSerializer
from mist.views.match import MatchRequestView, MatchView

from users.models import User
from users.serializers import ReadOnlyUserSerializer
from users.tests.generics import create_dummy_user_and_token_given_id

class NotificationServiceMock:
    sent_notifications = []

    def send_fake_notification(self, message, *args, **kwargs):
        NotificationServiceMock.sent_notifications.append(message)

@freeze_time("2020-01-01")
@patch('push_notifications.models.APNSDeviceQuerySet.send_message', 
    NotificationServiceMock.send_fake_notification)
class MatchRequestTest(TestCase):
    def setUp(self):
        NotificationServiceMock.sent_notifications = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )
        return

    def test_serializer_returns_computed_properties(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data
        properties = (
            'id', 
            'match_requesting_user',
            'match_requested_user',
            'post', 
            'read_only_post',
            'timestamp')
        for property in properties:
            self.assertTrue(property in serialized_match_request)
    
    def test_get_should_return_match_requests_given_valid_requesting_user(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        request = APIRequestFactory().get(
            '/api/match_requests',
            {
                'match_requesting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'get':'list'})(request)
        response_match_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_match_request, serialized_match_request)
        return
    
    def test_get_should_not_return_match_requests_given_invalid_requesting_user(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        request = APIRequestFactory().get(
            '/api/match_requests',
            {
                'match_requesting_user': self.user2.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        return

    def test_get_should_return_match_requests_with_deleted_post(self):
        pre_delete_match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        
        self.post.delete()

        post_delete_match_request = MatchRequest.objects.get(
            id=pre_delete_match_request.id)
        serialized_match_request = MatchRequestSerializer(post_delete_match_request).data

        request = APIRequestFactory().get(
            '/api/match_requests',
            {
                'match_requesting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'get':'list'})(request)
        response_match_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_match_request, serialized_match_request)
        return
    
    def test_post_should_create_match_request_given_valid_match_request(self):
        match_request = MatchRequest(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            match_requested_user=match_request.match_requested_user,
            post=self.post,
        ))

        request = APIRequestFactory().post(
            '/api/match_requests',
            serialized_match_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            match_requested_user=match_request.match_requested_user,
            post=self.post,
        ))
        return

    def test_post_should_send_device_notification_given_valid_match_request(self):
        match_request = MatchRequest(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            match_requested_user=match_request.match_requested_user,
            post=self.post,
        ))
        self.assertFalse(NotificationServiceMock.sent_notifications)

        request = APIRequestFactory().post(
            '/api/match_requests',
            serialized_match_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NotificationServiceMock.sent_notifications)
        return
    
    def test_post_should_not_create_match_request_given_invalid_match_request(self):
        match_request = MatchRequest(
            match_requesting_user=self.user1,
            post=self.post,
        )
        serialized_match_request = MatchRequestSerializer(match_request).data

        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            post=match_request.post,
        ))

        request = APIRequestFactory().post(
            '/api/match_requests',
            serialized_match_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(MatchRequest.objects.filter(
            match_requesting_user=match_request.match_requesting_user,
            post=match_request.post,
        ))
        return
    
    def test_delete_should_delete_match_request_given_pk(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            '/api/match_requests',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request, pk=match_request.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MatchRequest.objects.filter(pk=match_request.pk))
        return

    def test_delete_should_delete_favorite_given_query_combo(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            f'/api/match_requests?match_requesting_user={self.user1.pk}&match_requested_user={self.user2.pk}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MatchRequest.objects.filter(pk=match_request.pk))
        return
    
    def test_delete_should_not_delete_favorite_given_invalid_query_combo(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            f'/api/match_requests?match_requesting_user={self.user2.pk}&match_requested_user={self.user1.pk}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))
        return

    def test_delete_should_not_delete_favorite_given_nonexistent_pk(self):
        nonexistent_pk = 9999999
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))
        self.assertFalse(MatchRequest.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete(
            f'/api/match_requests',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))
        return

    def test_delete_should_not_delete_favorite_given_no_parameters(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            f'/api/match_requests',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))
        return

    def test_delete_should_delete_favorite_given_pk_and_query_combo(self):
        match_request = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        self.assertTrue(MatchRequest.objects.filter(pk=match_request.pk))

        request = APIRequestFactory().delete(
            f'/api/match_requests?match_requesting_user={self.user1.pk}&match_requested_user={self.user2.pk}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request, pk=match_request.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MatchRequest.objects.filter(pk=match_request.pk))
        return

    def test_delete_should_not_delete_favorite_given_invalid_pk_and_query_combo(self):
        match_request_1 = MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        match_request_2 = MatchRequest.objects.create(
            match_requesting_user=self.user2,
            match_requested_user=self.user1,
            post=self.post,
            timestamp=0,
        )

        request = APIRequestFactory().delete(
            f'/api/match_requests?match_requesting_user={self.user1.pk}&match_requested_user={self.user2.pk}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchRequestView.as_view({'delete':'destroy'})(request, pk=match_request_2.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(MatchRequest.objects.filter(pk=match_request_1.pk))
        self.assertTrue(MatchRequest.objects.filter(pk=match_request_2.pk))
        return

class MatchViewTest(TestCase):
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

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
            timestamp=0,
        )

        MatchRequest.objects.create(
            match_requesting_user=self.user2,
            match_requested_user=self.user1,
            post=self.post,
            timestamp=0,
        )

        MatchRequest.objects.create(
            match_requesting_user=self.user1,
            match_requested_user=self.user2,
            post=self.post,
            timestamp=0,
        )
        return

    def test_get_should_return_user1_given_user2(self):
        serialized_user1 = ReadOnlyUserSerializer(self.user1).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = MatchView.as_view()(request)
        response_user1 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user1, serialized_user1)
        return

    def test_get_should_return_user2_given_user1(self):
        serialized_user2 = ReadOnlyUserSerializer(self.user2).data

        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = MatchView.as_view()(request)
        response_user2 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user2, serialized_user2)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
        )
        response = MatchView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return