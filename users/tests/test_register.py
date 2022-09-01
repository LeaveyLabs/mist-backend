from datetime import date, datetime, timedelta
from django.core import mail, cache
from django.test import TestCase
from users.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from users.tests.generics import create_dummy_user_and_token_given_id

from users.views.register import RegisterPhoneNumberView, RegisterUserEmailView, ValidatePhoneNumberView, ValidateUserEmailView, ValidateUsernameView
from users.models import Ban, EmailAuthentication, PhoneNumberAuthentication, User

import sys
sys.path.append("..")
from twilio_config import TwillioTestClientMessages

class RegisterUserEmailViewTest(TestCase):
    def setUp(self):
        cache.cache.clear()

    def test_post_should_register_valid_email(self):
        fake_email = 'RegisterThisFakeEmail@usc.edu'

        self.assertFalse(EmailAuthentication.objects.filter(
            email__iexact=fake_email))

        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': fake_email,
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)
        email_auths = EmailAuthentication.objects.filter(
            email__iexact=fake_email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(email_auths)
        self.assertTrue(mail.outbox)
        self.assertEqual(mail.outbox[0].to[0], fake_email.lower())
        self.assertTrue(mail.outbox[0].body.find(str(email_auths[0].code)))
        return
    
    def test_post_should_not_register_invalid_email(self):
        invalid_email = 'ThisIsAnInvalidEmail'

        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': invalid_email,
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.filter(
            email__iexact='ThisIsAnInvalidEmail'))
        self.assertFalse(mail.outbox)
        return

    def test_post_should_not_register_banned_email(self):
        fake_email = 'RegisterThisFakeEmail@usc.edu'
        Ban.objects.create(email=fake_email.lower())

        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': fake_email,
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.filter(email__iexact=fake_email))
        self.assertFalse(mail.outbox)
        return

    def test_post_should_delete_existing_email_auth_given_existing_email(self):
        valid_email = "thisIsAValidEmail@usc.edu"
        old_email_auth = EmailAuthentication.objects.create(email=valid_email)

        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': valid_email,
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)
        new_email_auth = EmailAuthentication.objects.get(email__iexact=valid_email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(new_email_auth.code_time, old_email_auth.code_time)

class ValidateUserEmailViewTest(TestCase):
    def test_post_should_accept_valid_code(self):
        email_to_validate = 'ValidateThisFakeEmail@usc.edu'
        registration = EmailAuthentication(
            email=email_to_validate,
        )
        registration.save()

        self.assertFalse(EmailAuthentication.objects.get(
            email__iexact=email_to_validate).validated)

        request = APIRequestFactory().post('api-validate/',
            {
                'email': email_to_validate,
                'code': registration.code,
            },
            format='json',
        )
        response = ValidateUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(EmailAuthentication.objects.get(
            email__iexact=email_to_validate).validated)
        return
    
    def test_post_should_not_accept_invalid_code(self):
        email_to_validate = 'ValidateThisFakeEmail@usc.edu'
        registration = EmailAuthentication(
            email=email_to_validate,
        )
        registration.save()

        self.assertFalse(EmailAuthentication.objects.get(
            email=email_to_validate).validated)

        request = APIRequestFactory().post(
            'api-validate/',
            {
                'email': email_to_validate,
                'code': int(registration.code)+1,
            },
            format='json',
        )
        response = ValidateUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.get(
            email__iexact=email_to_validate).validated)
        return
    
    def test_post_should_not_accept_expired_code(self):
        email_to_validate = 'ValidateThisFakeEmail@usc.edu'
        now = datetime.now().timestamp()
        ten_minutes = timedelta(minutes=10).total_seconds()
        registration = EmailAuthentication(
            email=email_to_validate,
            code_time=now-ten_minutes,
        )
        registration.save()

        self.assertFalse(EmailAuthentication.objects.get(
            email=email_to_validate).validated)

        request = APIRequestFactory().post(
            'api-validate/',
            {
                'email': email_to_validate,
                'code': int(registration.code),
            },
            format='json',
        )
        response = ValidateUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.get(
            email__iexact=email_to_validate).validated)
        return

class ValidateUsernameViewTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        return
    
    def test_post_should_accept_untaken_username(self):
        untaken_username = 'untakenUsername'
        self.assertFalse(User.objects.filter(username=untaken_username))

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': untaken_username,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(username=untaken_username))
        return
    
    def test_post_should_not_accept_taken_username(self):
        taken_username = self.user1.username

        self.assertTrue(User.objects.filter(username=taken_username))

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': taken_username,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(username=taken_username))
        return
    
    def test_post_should_not_accept_identical_but_lowercase_username(self):
        all_lowercased_username = self.user1.username.lower()

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': all_lowercased_username,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(username__iexact=all_lowercased_username))
        return
    
    def test_post_should_not_accept_identical_but_uppercase_username(self):
        all_lowercased_username = self.user1.username.upper()

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': all_lowercased_username,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(username__iexact=all_lowercased_username))
        return

    def test_post_should_not_accept_special_characters(self):
        nonexisting_letters_numbers = '@#$$$$$'

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': nonexisting_letters_numbers,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_post_should_accept_periods_and_underscores(self):
        period_and_underscore = '._'

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': period_and_underscore,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return

    # def test_post_should_not_accept_profanity(self):
    #     profanity = 'fuck'

    #     request = APIRequestFactory().post(
    #         'api-validate-username/',
    #         {
    #             'username': profanity,
    #         },
    #         format='json',
    #     )
    #     response = ValidateUsernameView.as_view()(request)

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     return

    # def test_post_should_not_accept_hate_speech(self):
    #     hate_speech = 'nigger'

    #     request = APIRequestFactory().post(
    #         'api-validate-username/',
    #         {
    #             'username': hate_speech,
    #         },
    #         format='json',
    #     )
    #     response = ValidateUsernameView.as_view()(request)

    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     return

class RegisterPhoneNumberViewTest(TestCase):
    def setUp(self):
        TwillioTestClientMessages.created = []

        self.strong_password = 'newPassword@3312$5'
        self.unused_email = "notUsedEmail@usc.edu"

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        return

    def test_post_should_send_code_given_unused_and_valid_phone_number(self):
        valid_phone_number = "+12136569000"

        request = APIRequestFactory().post(
            'api/register-phone-number/',
            {
                'email': self.unused_email,
                'phone_number': valid_phone_number,
            },
        )
        response = RegisterPhoneNumberView.as_view()(request)
        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == valid_phone_number 
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(messages)
        self.assertTrue(matching_messages)
        return
    
    def test_post_should_send_code_given_multiple_registrations(self):
        valid_phone_number = "+12136569000"

        request = APIRequestFactory().post(
            'api/register-phone-number/',
            {
                'email': self.unused_email,
                'phone_number': valid_phone_number,
            },
        )
        response = RegisterPhoneNumberView.as_view()(request)
        response = RegisterPhoneNumberView.as_view()(request)

        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == valid_phone_number 
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(messages)
        self.assertTrue(matching_messages)
        return
    
    def test_post_should_not_send_code_given_used_email(self):
        valid_phone_number = "+12136569000"

        request = APIRequestFactory().post(
            'api/register-phone-number/',
            {
                'email': self.user1.email,
                'phone_number': valid_phone_number,
            },
        )
        response = RegisterPhoneNumberView.as_view()(request)

        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == valid_phone_number
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
    
    def test_post_should_not_send_code_given_invalid_phone_number(self):
        invalid_phone_number = "invalidPhoneNumber"

        request = APIRequestFactory().post(
            'api/register-phone-number/',
            {
                'email': self.unused_email,
                'phone_number': invalid_phone_number,
            },
        )
        response = RegisterPhoneNumberView.as_view()(request)

        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == invalid_phone_number
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return
    
    def test_post_should_not_send_code_given_used_phone_number(self):
        request = APIRequestFactory().post(
            'api/register-phone-number/',
            {
                'email': self.unused_email,
                'phone_number': self.user1.phone_number,
            },
        )
        response = RegisterPhoneNumberView.as_view()(request)

        messages = TwillioTestClientMessages.created
        matching_messages = [
            message.get('to') == self.user1.phone_number
            for message in messages
        ]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(matching_messages)
        return

class ValidatePhoneNumberViewTest(TestCase):    
    def test_post_should_return_success_given_matching_code(self):
        PhoneNumberAuthentication.objects.create(
            email="email@usc.edu",
            phone_number="+12136879999",
            code="123456",
        )

        request = APIRequestFactory().post(
            'api/validate-phone-number/',
            {
                'phone_number': '+12136879999',
                'code': '123456',
            },
        )
        response = ValidatePhoneNumberView.as_view()(request)
        authentication = PhoneNumberAuthentication.objects.filter(
            email='email@usc.edu')[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(authentication.validated)
        return

    def test_post_should_not_return_success_given_nonmatching_code(self):
        PhoneNumberAuthentication.objects.create(
            email="email@usc.edu",
            phone_number="+12136879999",
            code="123456",
        )

        request = APIRequestFactory().post(
            'api/validate-phone-number/',
            {
                'phone_number': '+12136879999',
                'code': '999999',
            },
        )
        response = ValidatePhoneNumberView.as_view()(request)
        authentication = PhoneNumberAuthentication.objects.filter(
            email='email@usc.edu')[0]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(authentication.validated)
        return
    
    def test_post_should_not_return_success_given_expired_code(self):
        now = datetime.now().timestamp()
        ten_minutes = timedelta(minutes=10).total_seconds()

        PhoneNumberAuthentication.objects.create(
            email="email@usc.edu",
            phone_number="+12136879999",
            code="123456",
            code_time=now-ten_minutes,
        )

        request = APIRequestFactory().post(
            'api/validate-phone-number/',
            {
                'phone_number': '+12136879999',
                'code': '999999',
            },
        )
        response = ValidatePhoneNumberView.as_view()(request)
        authentication = PhoneNumberAuthentication.objects.filter(
            email='email@usc.edu')[0]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(authentication.validated)
        return