import random
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIRequestFactory
from mist.models import AccessCode, Badge
from mist.views.access_code import ClaimAccessCodeView

from users.tests.generics import create_dummy_user_and_token_given_id

@freeze_time("2020-01-01")
class AccessCodeTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)

    def test_get_should_return_empty_list_given_nonexistent_code(self):
        nonexistent_code = "nonexistentCode"
        
        request = APIRequestFactory().get(
            f'api/access-codes/?code={nonexistent_code}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

    def test_get_should_return_empty_list_given_claimed_code(self):
        claimed_code = "123456"

        AccessCode.objects.create(
            code_string=claimed_code,
            claimed_user=self.user1,
        )
        
        request = APIRequestFactory().get(
            f'api/access-codes/?code={claimed_code}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

    def test_get_should_return_list_given_unclaimed_code(self):
        accessCodes = AccessCode.objects.all()
        accessCode = random.choice(accessCodes)
        code = accessCode.code_string
        
        request = APIRequestFactory().get(
            f'api/access-codes/?code={code}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)
        return
    
    def test_post_should_claim_code_given_correct_code_and_unclaimed_user(self):
        accessCodes = AccessCode.objects.all()
        accessCode = random.choice(accessCodes)
        code = accessCode.code_string

        request = APIRequestFactory().post(
            'api/access-codes/',
            {
                "code": accessCode.code_string,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        claimed_access_code = AccessCode.objects.filter(code_string=code, claimed_user=self.user1)
        claimed_badge = Badge.objects.filter(badge_type=Badge.LOVE_MIST, user=self.user1)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(claimed_access_code)
        self.assertTrue(claimed_badge)
        return

    def test_post_should_not_claim_code_given_incorrect_code_and_unclaimed_user(self):
        incorrect_code = "thisIsNotACorrectCode"

        request = APIRequestFactory().post(
            'api/access-codes/',
            {
                "code": incorrect_code,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        claimed_access_code = AccessCode.objects.filter(claimed_user=self.user1)
        claimed_badge = Badge.objects.filter(badge_type=Badge.LOVE_MIST, user=self.user1)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(claimed_access_code)
        self.assertFalse(claimed_badge)
        return

    def test_post_should_not_claim_code_given_correct_code_and_claimed_user(self):
        accessCodes = AccessCode.objects.all()
        accessCode = random.choice(accessCodes)
        code = accessCode.code_string

        AccessCode.objects.create(
            claimed_user=self.user1,
        )

        request = APIRequestFactory().post(
            'api/access-codes/',
            {
                "code": code,
            },
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = ClaimAccessCodeView.as_view()(request)
        claimed_access_code = AccessCode.objects.filter(code_string=code, claimed_user=self.user1)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(claimed_access_code)
        return