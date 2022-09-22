import random
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIRequestFactory
from mist.models import Collectible
from mist.views.collectible import ClaimCollectibleView

from users.tests.generics import create_dummy_user_and_token_given_id

@freeze_time("2020-01-01")
class CollectibleTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

        self.test_collectible = 0

    def test_post_should_create_collectible_given_unclaimed_collectible_type(self):
        request = APIRequestFactory().post(
            'api/collectibles/',
            {
                'collectible_type': self.test_collectible,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimCollectibleView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Collectible.objects.filter(
            user=self.user1,
            collectible_type=self.test_collectible,
        ))
        return

    def test_post_should_not_create_collectible_given_claimed_collectible_type(self):
        Collectible.objects.create(
            user=self.user1,
            collectible_type=self.test_collectible,
        )
        
        request = APIRequestFactory().post(
            'api/collectibles/',
            {
                'collectible_type': self.test_collectible,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimCollectibleView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Collectible.objects.filter(
            user=self.user1,
            collectible_type=self.test_collectible,).count(), 1)
        return

    def test_post_should_not_create_collectible_given_invalid_collectible_type(self):
        request = APIRequestFactory().post(
            'api/collectibles/',
            {
                'collectible_type': -1,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimCollectibleView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Collectible.objects.filter(
            user=self.user1,
            collectible_type=self.test_collectible,
        ))
        return