from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import FriendRequest, Post
from mist.serializers import FriendRequestSerializer
from mist.views.friend import FriendRequestView, FriendshipView

from users.models import User
from users.serializers import ReadOnlyUserSerializer

@freeze_time("2020-01-01")
class FriendRequestTest(TestCase):
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

    def test_get_should_return_friend_request_given_valid_friend_requesting_user(self):
        friend_request1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request2 = FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user3,
            timestamp=0,
        )
        serialized_friend_request1 = FriendRequestSerializer(friend_request1).data
        serialized_friend_request2 = FriendRequestSerializer(friend_request2).data
        
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requesting_user': friend_request1.friend_requesting_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_friend_request, serialized_friend_request1)
        return
    
    def test_get_should_not_return_friend_request_given_invalid_friend_requesting_user(self):
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requesting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_requests = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_friend_requests)
        return
    
    def test_get_should_return_friend_request_given_valid_friend_requested_user(self):
        friend_request1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request2 = FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user3,
            timestamp=0,
        )
        serialized_friend_request1 = FriendRequestSerializer(friend_request1).data
        serialized_friend_request2 = FriendRequestSerializer(friend_request2).data
        
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requested_user': friend_request1.friend_requested_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_request = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_friend_request, serialized_friend_request1)
        return
    
    def test_get_should_not_return_friend_request_given_invalid_friend_requested_user(self):
        request = APIRequestFactory().get(
            '/api/friend_request',
            {
                'friend_requested_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'get':'list'})(request)
        response_friend_requests = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_friend_requests)
        return
    
    def test_post_should_create_friend_request_given_valid_friend_request(self):
        friend_request = FriendRequest(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        serialized_friend_request = FriendRequestSerializer(friend_request).data

        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
            friend_requested_user=friend_request.friend_requested_user,
        ))

        request = APIRequestFactory().post(
            '/api/friend_request/',
            serialized_friend_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'post':'create'})(request)
        response_friend_request = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_friend_request.get('friend_requesting_user'), 
                        serialized_friend_request.get('friend_requesting_user'))
        self.assertEqual(response_friend_request.get('friend_requested_user'), 
                        serialized_friend_request.get('friend_requested_user'))
        self.assertTrue(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
            friend_requested_user=friend_request.friend_requested_user,
        ))
        return
    
    def test_post_should_not_create_friend_request_given_invalid_friend_request(self):
        friend_request = FriendRequest(
            friend_requesting_user=self.user1,
        )
        serialized_friend_request = FriendRequestSerializer(friend_request).data

        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
        ))

        request = APIRequestFactory().post(
            '/api/friend_request/',
            serialized_friend_request,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FriendRequestView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(FriendRequest.objects.filter(
            friend_requesting_user=friend_request.friend_requesting_user,
        ))
        return
    
    def test_delete_should_delete_friend_request_given_pk(self):
        friend_request = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))

        request = APIRequestFactory().delete('/api/friend_request/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk=friend_request.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FriendRequest.objects.filter(pk=friend_request.pk))
        return
    
    def test_delete_should_delete_friend_request_given_query_combo(self):
        friend_request = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))

        request = APIRequestFactory().delete(
            f'/api/friend_request/?friend_requesting_user={self.user1.pk}&friend_requested_user={self.user2.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FriendRequest.objects.filter(pk=friend_request.pk))
        return
    
    def test_delete_should_delete_friend_request_given_no_parameters(self):
        friend_request = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))

        request = APIRequestFactory().delete(
            f'/api/friend_request/', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))
        return
    
    def test_delete_should_not_delete_friend_request_given_nonexistent_pk(self):
        nonexistent_pk = 999999
        self.assertFalse(FriendRequest.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete(
            f'/api/friend_request/', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(FriendRequest.objects.filter(pk=nonexistent_pk))
        return
    
    def test_delete_should_not_delete_friend_request_given_invalid_query_combo(self):
        friend_request = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))

        request = APIRequestFactory().delete(
            f'/api/friend_request/?friend_requesting_user={self.user2.pk}&friend_requested_user={self.user1.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request.pk))
        return
    
    def test_delete_should_delete_friend_request_with_pk_given_both_pk_and_query_combo(self):
        friend_request_1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request_2 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user3,
            timestamp=0,
        )

        self.assertTrue(FriendRequest.objects.filter(pk=friend_request_1.pk))
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request_2.pk))

        request = APIRequestFactory().delete(
            f'/api/friend_request/?friend_requesting_user={self.user1.pk}&friend_requested_user={self.user2.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk=friend_request_1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FriendRequest.objects.filter(pk=friend_request_1.pk))
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request_2.pk))
        return
    
    def test_delete_should_not_delete_friend_request_given_invalid_pk_and_query_combo(self):
        friend_request_1 = FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )
        friend_request_2 = FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user1,
            timestamp=0,
        )

        request = APIRequestFactory().delete(
            f'/api/friend_request/?friend_requesting_user={self.user1.pk}&friend_requested_user={self.user2.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FriendRequestView.as_view({'delete':'destroy'})(request, pk=friend_request_2.pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request_1.pk))
        self.assertTrue(FriendRequest.objects.filter(pk=friend_request_2.pk))
        return

class FriendshipViewTest(TestCase):
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

        FriendRequest.objects.create(
            friend_requesting_user=self.user1,
            friend_requested_user=self.user2,
            timestamp=0,
        )

        FriendRequest.objects.create(
            friend_requesting_user=self.user2,
            friend_requested_user=self.user1,
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
        response = FriendshipView.as_view()(request)
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
        response = FriendshipView.as_view()(request)
        response_user2 = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user2, serialized_user2)
        return
    
    def test_get_should_not_return_anything_given_stranger(self):
        request = APIRequestFactory().get(
            '/api/matches',
            format='json',
        )
        response = FriendshipView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return
