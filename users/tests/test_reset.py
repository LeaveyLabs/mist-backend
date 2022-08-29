from datetime import date, timedelta
from django.core import mail
from django.test import TestCase
from users.generics import get_current_time
from users.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory

from users.views.reset import RequestResetEmailView, RequestResetTextCodeView, ValidateResetEmailView, ValidateResetTextCodeView
from users.models import PasswordReset, PhoneNumberReset, User

import sys
sys.path.append("..")
from twilio_config import TwillioTestClientMessages

class RequestResetEmailViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678999"
        )
        self.unused_email = "thisEmailIsNotInUse@usc.edu"
        self.invalid_phone_number = "not-a-valid-phone-number"
        return
    
    def test_post_should_send_code_given_used_email(self):
        request = APIRequestFactory().post(
            'api/request-reset-email/',
            {
                'email': self.user1.email,
            }
        )
        response = RequestResetEmailView.as_view()(request)
        reset_requests = PhoneNumberReset.objects.filter(
            email=self.user1.email,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(reset_requests)
        self.assertTrue(mail.outbox)
        self.assertEqual(mail.outbox[0].to[0], self.user1.email.lower())
        self.assertTrue(mail.outbox[0].body.find(str(reset_requests[0].email_code)))
        return

    def test_post_should_not_send_code_given_unused_email(self):
        request = APIRequestFactory().post(
            'api/request-reset-email/',
            {
                'email': self.unused_email,
            }
        )
        response = RequestResetEmailView.as_view()(request)
        reset_requests = PasswordReset.objects.filter(
            email=self.unused_email,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(reset_requests)
        self.assertFalse(mail.outbox)
        return

class ValidateResetEmailViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678999"
        )
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.reset = PhoneNumberReset.objects.create(
            email=self.user1.email,
        )

        self.unrequested_email = "thisEmailWasNotRequested@usc.edu"
        self.invalid_code = "thisCodeIsNotValid"
        return

    def test_post_should_return_success_given_requested_email_and_valid_code(self):
        request = APIRequestFactory().post(
            'api/validate-reset-email/',
            {
                'email': self.reset.email,
                'code': self.reset.email_code,
            }
        )
        response = ValidateResetEmailView.as_view()(request)
        response_token = response.data.get('token')
        expected_token = PhoneNumberReset.objects.get(email=self.reset.email).reset_token

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_token, expected_token)
        self.assertTrue(PhoneNumberReset.objects.get(email=self.reset.email).email_validated)
        return

    def test_post_should_return_failure_given_unrequested_email_and_valid_code(self):
        request = APIRequestFactory().post(
            'api/validate-reset-email/',
            {
                'email': self.unrequested_email,
                'code': self.reset.email_code,
            }
        )
        response = ValidateResetEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(PhoneNumberReset.objects.get(email=self.reset.email).email_validated)
        return

    def test_post_should_return_failure_given_requested_email_and_invalid_code(self):
        request = APIRequestFactory().post(
            'api/validate-reset-email/',
            {
                'email': self.reset.email,
                'code': self.invalid_code,
            }
        )
        response = ValidateResetEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(PhoneNumberReset.objects.get(email=self.reset.email).email_validated)
        return

    def test_post_should_return_failure_given_unrequested_email_and_invalid_code(self):
        request = APIRequestFactory().post(
            'api/validate-reset-email/',
            {
                'email': self.unrequested_email,
                'code': self.invalid_code,
            }
        )
        response = ValidateResetEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(PhoneNumberReset.objects.get(email=self.reset.email).email_validated)
        return
    
    def test_post_should_return_failure_given_requested_email_and_expired_code(self):
        now = get_current_time()
        ten_minutes = timedelta(minutes=10).total_seconds()
        self.reset.email_code_time = now - ten_minutes
        self.reset.save()

        request = APIRequestFactory().post(
            'api/validate-reset-email/',
            {
                'email': self.reset.email,
                'code': self.reset.email_code,
            }
        )
        response = ValidateResetEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        self.assertFalse(PhoneNumberReset.objects.get(email=self.reset.email).email_validated)
        return

class RequestResetTextCodeViewTest(TestCase):
    def setUp(self):
        TwillioTestClientMessages.created = []

        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678999"
        )
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User.objects.create(
            email="email2@usc.edu",
            username="unrelatedUsername2",
            first_name="completelyDifferentFirstName2",
            last_name="notTheSameLastName2",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678998"
        )
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.reset = PhoneNumberReset.objects.create(
            email=self.user1.email,
            email_validated=True,
            email_validation_time=get_current_time(),
        )

        self.unvalidated_email = "unvalidatedEmail@usc.edu"
        self.invalid_phone_number = "not-a-valid-phone-number"
        self.valid_phone_number = "+12345678997"
        return

    def test_post_should_send_code_given_validated_email_and_valid_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.valid_phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.valid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(matching_messages)
        return
    
    def test_post_should_not_send_code_given_used_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.user1.phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.valid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return
    
    def test_post_should_not_send_code_without_token(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.valid_phone_number,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.valid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return
    
    def test_post_should_not_send_code_with_invalid_token(self):
        invalid_token = 'invalidToken'
        
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.valid_phone_number,
                'token': invalid_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.valid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

    def test_post_should_not_send_code_given_unvalidated_email_and_valid_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.unvalidated_email,
                'phone_number': self.valid_phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.valid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

    def test_post_should_not_send_code_given_validated_email_and_invalid_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.invalid_phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.invalid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

    def test_post_should_not_send_code_given_unvalidated_email_and_invalid_phone_number(self):
        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.unvalidated_email,
                'phone_number': self.invalid_phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.invalid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return
    
    def test_post_should_not_send_code_given_expired_email_and_valid_phone_number(self):
        now = get_current_time()
        ten_minutes = timedelta(minutes=10).total_seconds()
        self.reset.email_validation_time = now - ten_minutes
        self.reset.save()

        request = APIRequestFactory().post(
            'api/request-phone-number/',
            {
                'email': self.reset.email,
                'phone_number': self.invalid_phone_number,
                'token': self.reset.reset_token,
            },
        )
        response = RequestResetTextCodeView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == self.invalid_phone_number:
                matching_messages.append(message)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

class ValidateResetTextCodeViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678999"
        )

        self.new_phone_number = "+13108889999"

        self.reset = PhoneNumberReset.objects.create(
            email=self.user1.email,
            email_validated=True,
            email_validation_time=get_current_time(),
            phone_number=self.new_phone_number,
        )

        self.unrequested_phone_number = "+9987654321"
        self.invalid_code = "not-a-valid-code"
        return
    
    def test_post_should_return_success_given_requested_phone_number_and_valid_code(self):
        request = APIRequestFactory().post(
            'api/validate-phone-number',
            {
                'phone_number': str(self.reset.phone_number),
                'code': self.reset.phone_number_code,
                'token': self.reset.reset_token,
            }
        )
        response = ValidateResetTextCodeView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            PhoneNumberReset.objects.get(email=self.reset.email).phone_number_validated
        )
        self.assertEqual(
            User.objects.get(email=self.reset.email).phone_number, 
            self.new_phone_number,
        )
        return

    def test_post_should_return_failure_given_unrequested_phone_number_and_valid_code(self):
        request = APIRequestFactory().post(
            'api/validate-phone-number',
            {
                'phone_number': str(self.unrequested_phone_number),
                'code': self.reset.phone_number_code,
                'token': self.reset.reset_token,
            }
        )
        response = ValidateResetTextCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PhoneNumberReset.objects.get(email=self.user1.email).phone_number_validated
        )
        self.assertNotEqual(
            User.objects.get(email=self.user1.email).phone_number, 
            self.new_phone_number,
        )
        return

    def test_post_should_return_failure_given_unrequested_phone_number_and_valid_code(self):
        request = APIRequestFactory().post(
            'api/validate-phone-number',
            {
                'phone_number': str(self.reset.phone_number),
                'code': self.invalid_code,
                'token': self.reset.reset_token,
            }
        )
        response = ValidateResetTextCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PhoneNumberReset.objects.get(email=self.user1.email).phone_number_validated
        )
        self.assertNotEqual(
            User.objects.get(email=self.user1.email).phone_number, 
            self.new_phone_number,
        )
        return

    def test_post_should_return_failure_given_unrequested_phone_number_and_invalid_code(self):
        request = APIRequestFactory().post(
            'api/validate-phone-number',
            {
                'phone_number': str(self.unrequested_phone_number),
                'code': self.invalid_code,
                'token': self.reset.reset_token,
            }
        )
        response = ValidateResetTextCodeView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PhoneNumberReset.objects.get(email=self.user1.email).phone_number_validated
        )
        self.assertNotEqual(
            User.objects.get(email=self.user1.email).phone_number, 
            self.new_phone_number,
        )
        return

    def test_post_should_return_failure_given_requested_phone_number_and_expired_code(self):
        now = get_current_time()
        ten_minutes = timedelta(minutes=10).total_seconds()
        self.reset.phone_number_code_time = now - ten_minutes
        self.reset.save()

        request = APIRequestFactory().post(
            'api/validate-phone-number',
            {
                'phone_number': str(self.reset.phone_number),
                'code': self.reset.phone_number_code,
                'token': self.reset.reset_token,
            }
        )
        response = ValidateResetTextCodeView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            PhoneNumberReset.objects.get(email=self.user1.email).phone_number_validated
        )
        self.assertNotEqual(
            User.objects.get(email=self.user1.email).phone_number, 
            self.new_phone_number,
        )
        return