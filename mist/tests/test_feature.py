from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Feature, Post
from mist.serializers import FeatureSerializer
from mist.views.feature import FeatureView

from users.models import User

@freeze_time("2020-01-01")
class FeatureTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )
        return
    
    def test_get_should_return_all_features_given_no_parameters(self):
        feature = Feature.objects.create(
            timestamp=0,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return

    def test_get_should_return_features_with_timestamp_given_valid_timestamp(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'timestamp': feature.timestamp,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return
    
    def test_get_should_not_return_features_with_timestamp_given_invalid_timestamp(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'timestamp': feature.timestamp-1,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_get_should_return_features_with_post_given_valid_post(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'post': feature.post.pk,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)
        response_feature = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_feature, serialized_feature)
        return
    
    def test_get_should_not_return_features_with_timestamp_given_invalid_post(self):
        feature = Feature.objects.create(
            timestamp=1,
            post=self.post,
        )
        serialized_feature = FeatureSerializer(feature).data
        
        request = APIRequestFactory().get(
            '/api/features', 
            {
                'post': feature.post.pk-1,
            },
            format='json', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FeatureView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return