from datetime import datetime, timedelta
from django.test import TestCase
from users.generics import get_current_time
from users.models import Ban
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from users.tests.generics import create_dummy_user_and_token_given_id

from users.views.login import RequestLoginCodeView, ValidateLoginCodeView
from users.models import PhoneNumberAuthentication, User

import sys
sys.path.append("..")
from twilio_config import TwillioTestClientMessages

class RequestLoginCodeViewTest(TestCase):
    # phone number
    def setUp(self):
        TwillioTestClientMessages.created = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        
        PhoneNumberAuthentication.objects.create(
            phone_number=self.user1.phone_number,
            email=self.user1.email,
            validated=True,
            validation_time=get_current_time(),
        )
        return

    def test_post_should_send_code_given_used_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': str(self.user1.phone_number),
            },
        )
        response = RequestLoginCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == self.user1.phone_number
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(matching_messages)
        return
    
    def test_post_should_not_send_code_given_invalid_phone_number(self):
        invalid_phone_number = "invalidPhoneNumber"

        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': invalid_phone_number,
            },
        )
        response = RequestLoginCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == self.user1.phone_number
            for message in messages
        ]
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

    def test_post_should_not_send_code_given_banned_phone_number(self):
        banned_phone_number = "+13108741292"

        self.user1.phone_number = banned_phone_number
        self.user1.save()

        Ban.objects.create(phone_number=self.user1.phone_number)

        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': banned_phone_number,
            },
        )
        response = RequestLoginCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == self.user1.phone_number
            for message in messages
        ]
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

    def test_post_should_not_send_code_given_unused_phone_number(self):
        unused_phone_number = "+11234567890"

        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': unused_phone_number,
            },
        )
        response = RequestLoginCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == self.user1.phone_number
            for message in messages
        ]
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return
    
class ValidateLoginCodeViewTest(TestCase):
    def setUp(self):
        TwillioTestClientMessages.created = []

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        
        self.phone_number_auth = PhoneNumberAuthentication.objects.create(
            phone_number=self.user1.phone_number,
            email=self.user1.email,
            code="123456",
            code_time=get_current_time(),
            validated=True,
            validation_time=get_current_time(),
        )
        return

    def test_post_should_return_token_given_valid_phone_number_and_code_combo(self):
        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': str(self.user1.phone_number),
                'code': '123456',
            },
        )
        response = ValidateLoginCodeView.as_view()(request)
        response_token = response.data.get('token')
        expected_token = Token.objects.get(user=self.user1).key

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_token, expected_token)
        return
    
    def test_post_should_not_return_token_given_invalid_phone_number_and_code_combo(self):
        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': str(self.user1.phone_number),
                'code': '654321',
            },
        )
        response = ValidateLoginCodeView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_post_should_not_return_token_given_expired_phone_number_and_code_combo(self):
        now = datetime.now().timestamp()
        ten_minutes = timedelta(minutes=10).total_seconds()

        authentication = PhoneNumberAuthentication.objects.get(
            phone_number=self.user1.phone_number)
        authentication.code_time = now-ten_minutes
        authentication.save()

        request = APIRequestFactory().post(
            'api/request-login-code/',
            {
                'phone_number': str(self.user1.phone_number),
                'code': self.phone_number_auth.code,
            },
        )
        response = ValidateLoginCodeView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return