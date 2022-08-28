from datetime import date, datetime, timedelta
from io import BytesIO
from tempfile import TemporaryFile
from PIL import Image
from django.core import mail, cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.contrib.auth import authenticate
from users.generics import get_current_time
from users.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from .serializers import CompleteUserSerializer, ReadOnlyUserSerializer
from .views import FinalizePasswordResetView, LoginView, MatchingPhoneNumbersView, NearbyUsersView, RegisterPhoneNumberView, RegisterUserEmailView, RequestLoginCodeView, RequestPasswordResetView, RequestResetEmailView, RequestResetTextCodeView, UserView, ValidateLoginCodeView, ValidatePasswordResetView, ValidatePasswordView, ValidatePhoneNumberView, ValidateResetEmailView, ValidateResetTextCodeView, ValidateUserEmailView, ValidateUsernameView
from .models import Ban, PasswordReset, PhoneNumberAuthentication, PhoneNumberReset, User, EmailAuthentication

import sys
sys.path.append("..")
from twilio_config import TwillioTestClientMessages

# Create your tests here.
class ThrottleTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)

    def test_should_throttle_anonymous_user_above_50_calls(self):
        number_of_calls = 50
        self.run_fake_stranger_request(number_of_calls)

        number_of_email_registration_requests = len(mail.outbox)
        self.assertEqual(number_of_email_registration_requests, number_of_calls)
        
        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'validEmail@usc.edu',
            },
            format='json',
            
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        return
        
    def test_should_not_throttle_anonymous_user_at_or_below_50_calls(self):
        number_of_calls = 49
        self.run_fake_stranger_request(number_of_calls)

        number_of_email_registration_requests = len(mail.outbox)
        self.assertEqual(number_of_email_registration_requests, number_of_calls)
        
        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'validEmail@usc.edu',
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return

    def test_should_throttle_authenticated_user_above_200_calls(self):
        number_of_calls = 200
        self.run_fake_authenticated_user_request(number_of_calls)

        number_of_email_registration_requests = len(mail.outbox)
        self.assertEqual(number_of_email_registration_requests, number_of_calls)
        
        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'validEmail@usc.edu',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        return

    def test_should_not_throttle_authenticated_user_at_or_below_200_calls(self):
        number_of_calls = 199
        self.run_fake_authenticated_user_request(number_of_calls)

        number_of_email_registration_requests = len(mail.outbox)
        self.assertEqual(number_of_email_registration_requests, number_of_calls)
        
        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'validEmail@usc.edu',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return
    
    def run_fake_stranger_request(self, number_of_repeats):
        for _ in range(number_of_repeats):
            fake_request = APIRequestFactory().post(
                'api-register/',
                {
                    'email': 'validEmail@usc.edu',
                },
                format='json',
            )
            fake_response = RegisterUserEmailView.as_view()(fake_request)
    
    def run_fake_authenticated_user_request(self, number_of_repeats):
        for _ in range(number_of_repeats):
            fake_request = APIRequestFactory().post(
                'api-register/',
                {
                    'email': 'validEmail@usc.edu',
                },
                format='json',
                HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
            )
            fake_response = RegisterUserEmailView.as_view()(fake_request)
        

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
        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="takenUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
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
        taken_username = 'takenUsername'

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
        all_lowercased_username = 'takenusername'

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
        all_lowercased_username = 'TAKENUSERNAME'

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

    def test_post_should_not_accept_profanity(self):
        profanity = 'fuck'

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': profanity,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return

    def test_post_should_not_accept_hate_speech(self):
        hate_speech = 'nigger'

        request = APIRequestFactory().post(
            'api-validate-username/',
            {
                'username': hate_speech,
            },
            format='json',
        )
        response = ValidateUsernameView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return

class ValidatePasswordViewTest(TestCase):
    def setUp(self):
        cache.cache.clear()
        self.username = 'FakeTestingUsername'
        self.strong_password = 'FakeTestingPassword@3124587'
        self.short_passowrd = 'fff'
        self.generic_password = 'password'
        self.numerical_password = '1234567'
        self.username_password = 'FakeTestingUsername'
        return

    def test_post_should_accept_strong_password(self):
        request = APIRequestFactory().post(
            'api-validate-password/',
            {
                'username': self.username,
                'password': self.strong_password,
            },
            format='json',
        )
        response = ValidatePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_should_not_accept_password_under_9_characters(self):
        request = APIRequestFactory().post(
            'api-validate-password/',
            {
                'username': self.username,
                'password': self.short_passowrd,
            },
            format='json',
        )
        response = ValidatePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_should_not_accept_generic_password(self):
        request = APIRequestFactory().post(
            'api-validate-password/',
            {
                'username': self.username,
                'password': self.generic_password,
            },
            format='json',
        )
        response = ValidatePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_should_not_accept_only_numerical_password(self):
        request = APIRequestFactory().post(
            'api-validate-password/',
            {
                'username': self.username,
                'password': self.numerical_password,
            },
            format='json',
        )
        response = ValidatePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_should_not_accept_password_too_close_to_username(self):
        request = APIRequestFactory().post(
            'api-validate-password/',
            {
                'username': self.username,
                'password': self.username_password,
            },
            format='json',
        )
        response = ValidatePasswordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserViewPostTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.email_auth = EmailAuthentication.objects.create(
            email='thisEmailDoesExist@usc.edu',
        )
        self.email_auth.validated = True
        self.email_auth.validation_time = datetime.now().timestamp()
        self.email_auth.save()

        self.phone_auth = PhoneNumberAuthentication.objects.create(
            phone_number='+12134569999',
            email=self.email_auth.email,
        )
        self.phone_auth.validated = True
        self.phone_auth.validation_time = datetime.now().timestamp()
        self.phone_auth.save()

        self.fake_username = 'FakeTestingUsername'
        self.fake_first_name = 'FirstNameOfFakeUser'
        self.fake_last_name = 'LastNameOfFakeUser'
        self.fake_date_of_birth = date(2000, 1, 1)
        self.fake_keywords = ['These', 'Are', 'Fake', 'Keywords', 'Folks']

        test_image1 = Image.open('test_assets/test1.jpeg')
        test_image_io1 = BytesIO()
        test_image1.save(test_image_io1, format='JPEG')

        test_image2 = Image.open('test_assets/test2.jpeg')
        test_image_io2 = BytesIO()
        test_image2.save(test_image_io2, format='JPEG')

        self.image_file1 = SimpleUploadedFile('test1.jpeg', test_image_io1.getvalue(), content_type='image/jpeg')
        self.image_file2 = SimpleUploadedFile('test2.jpeg', test_image_io2.getvalue(), content_type='image/jpeg')

    def test_post_should_create_user_given_validated_email_and_validated_phone_number(self):
        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
                'picture': self.image_file1,
                'confirm_picture': self.image_file2,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.email_auth.email))
        self.assertTrue('token' in response.data)
        return

    def test_post_should_not_create_user_given_unvalidated_email(self):
        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
                'picture': self.image_file1,
                'confirm_picture': self.image_file1,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='thisEmailDoesNotExist@usc.edu'))
        return
    
    def test_post_should_not_create_user_given_unvalidated_phone_number(self):
        unvalidated_phone_number = "+12345678900"

        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': unvalidated_phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
                'picture': self.image_file1,
                'confirm_picture': self.image_file1,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='thisEmailDoesNotExist@usc.edu'))
        return
    
    def test_post_should_not_create_user_given_no_picture(self):
        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email=self.email_auth.email))
        return
    
    def test_post_should_not_create_user_given_expired_validation(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image_file = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')

        ten_minutes = timedelta(minutes=10).total_seconds()

        self.email_auth.validation_time -= ten_minutes
        self.email_auth.save()

        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
                'picture': self.image_file1,
                'confirm_picture': self.image_file1,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email=self.email_auth.email))
        return
    
    def test_post_should_not_create_user_given_user_under_age_18(self):
        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': date.today(),
                'picture': self.image_file1,
                'confirm_picture': self.image_file1,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email=self.email_auth.email))
        return

    def test_post_should_not_create_user_given_banned_email(self):
        Ban.objects.create(email=self.email_auth.email.lower())

        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': self.email_auth.email,
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': date.today(),
                'picture': self.image_file1,
                'confirm_picture': self.image_file1,
            }),
            content_type=MULTIPART_CONTENT,
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email=self.email_auth.email))
        return

class APITokenViewPostTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.fake_username = 'FakeTestingUsername'
        self.fake_email = 'thisEmailDoesExist@usc.edu'
        self.fake_password = 'FakeTestingPassword@3124587'
        self.fake_first_name = 'FirstNameOfFakeUser'
        self.fake_last_name = 'LastNameOfFakeUser'

        self.email_auth = EmailAuthentication.objects.create(
            email=self.fake_email,
        )
        self.email_auth.validated = True
        self.email_auth.validation_time = datetime.now().timestamp()
        self.email_auth.save()
        
    def test_post_should_obtain_token_given_valid_username_valid_password(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': self.fake_username, 
                'password': self.fake_password,
            },
            format='json',
        )
        response = LoginView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        return
    
    def test_post_should_obtain_token_given_valid_email_valid_password(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': self.fake_email, 
                'password': self.fake_password,
            },
            format='json',
        )
        response = LoginView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        return
    
    def test_post_should_not_obtain_token_given_invalid_username(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': 'ThisUserDoesNotExist', 
                'password': self.fake_password,
            },
            format='json',
        )
        response = LoginView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_post_should_not_obtain_token_given_invalid_email(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': 'thisEmailDoesNotExist@doesNotExist.usc.edu', 
                'password': self.fake_password,
            },
            format='json',
        )
        response = LoginView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_post_should_not_obtain_token_given_invalid_password(self):
        user = User(
            email= self.email_auth.email,
            username= self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': self.fake_username, 
                'password': 'ThisPasswordDoesNotExist',
            },
            format='json',
        )

        response = LoginView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_post_should_not_obtain_token_given_no_password(self):
        user = User(
            email= self.email_auth.email,
            username= self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'email_or_username': self.fake_username, 
            },
            format='json',
        )

        response = LoginView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_post_should_not_obtain_token_given_no_email_or_username(self):
        user = User(
            email= self.email_auth.email,
            username= self.fake_username,
            date_of_birth=date(2000, 1, 1),
        )
        user.set_password(self.fake_password)
        user.save()

        request = APIRequestFactory().post(
            'api-token/',
            {
                'password': self.fake_password,
            },
            format='json',
        )

        response = LoginView.as_view()(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return

class UserViewGetTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12136778889")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.user_serializer = CompleteUserSerializer(self.valid_user)

    # Serialization
    def test_get_should_return_readonly_user_given_nonmatching_token(self):
        non_matching_user = User.objects.create(
            email="nonMatchingEmail@usc.edu",
            username="nonMatchingUsername",
            first_name="thisFirstNameHasNotBeenTaken",
            last_name="thisLastNameHasNotBeenTaken",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678900")
        non_matching_user.set_password('nonMatchingPassword')
        non_matching_user.save()
        auth_token = Token.objects.create(user=non_matching_user)

        user_serializer = ReadOnlyUserSerializer(non_matching_user)

        request = APIRequestFactory().get(
            'api/users/',
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'retrieve'})(request, pk=non_matching_user.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, user_serializer.data)
        return
    
    def test_get_should_return_full_user_given_matching_token(self):
        request = APIRequestFactory().get(
            'api/users/',
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'retrieve'})(request, pk=self.valid_user.id)
        response_user = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_user, self.user_serializer.data)
        return

    # Valid Queries
    def test_get_should_return_user_given_word(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'words': 'name',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_case_insensitive_word(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'words': 'NAME',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_multiple_words(self):
        request = APIRequestFactory().get(
            'api/users/?words=name&words=not',
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelatedUsername',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelated',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completelyDifferentFirstName',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completely',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSameLastName',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return
        
    def test_get_should_return_user_given_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSame',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_valid_token(self):
        serialized_users = [self.user_serializer.data]

        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': self.auth_token,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users, serialized_users)
        return

    # Invalid User
    def test_get_should_not_return_user_given_nonexistent_words(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'words': 'notInTheTextAtAll',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

    def test_get_should_not_return_user_given_nonexistent_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'thisUsernameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_get_should_not_return_user_given_nonexistent_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'sername',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return

    def test_get_should_not_return_user_given_nonexistent_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'thisFirstNameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return
    
    def test_get_should_not_return_user_given_nonexistent_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'DifferentFirstName',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

    def test_get_should_not_return_user_given_nonexistent_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'thisLastNameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return

    def test_get_should_not_return_user_given_nonexistent_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'astName',
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return
    
    def test_get_should_not_return_user_given_invalid_token(self):
        invalid_token = "InvalidToken"
        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': invalid_token,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

class UserViewDeleteTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.unused_pk = 151

    def test_delete_should_delete_valid_user(self):
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))

        request = APIRequestFactory().delete('api/users/', HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.valid_user.pk))
        return

    def test_delete_should_not_delete_nonexistent_user(self):
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))

        request = APIRequestFactory().delete('api/users/', HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.unused_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))
        return

class UserViewPatchTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedusername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            latitude=0,
            longitude=0,
            phone_number="+11234567890")
        self.password = "strongPassword@1354689$"
        self.valid_user.set_password(self.password)
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.unused_pk = 151

        test_image1 = Image.open('test_assets/test1.jpeg')
        test_image_io1 = BytesIO()
        test_image1.save(test_image_io1, format='JPEG')

        test_image2 = Image.open('test_assets/test2.jpeg')
        test_image_io2 = BytesIO()
        test_image2.save(test_image_io2, format='JPEG')

        self.image_file1 = SimpleUploadedFile('test1.jpeg', test_image_io1.getvalue(), content_type='image/jpeg')
        self.image_file2 = SimpleUploadedFile('test2.jpeg', test_image_io2.getvalue(), content_type='image/jpeg')

    def test_patch_should_not_update_given_invalid_user(self):
        self.assertFalse(User.objects.filter(pk=self.unused_pk))

        request = APIRequestFactory().patch('api/users/', HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.unused_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(User.objects.filter(pk=self.unused_pk))
        return
        
    def test_patch_should_update_username_given_valid_username(self):
        self.assertEqual(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)
        fake_new_username = 'FakeNewUsername'

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': fake_new_username,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(fake_new_username.lower(), patched_user.username)
        self.assertTrue(patched_user.check_password(self.password))
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_not_update_username_given_invalid_username(self):
        self.assertEqual(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': "$%@#",
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertTrue(patched_user.check_password(self.password))
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_update_first_name_given_first_name(self):
        fake_first_name = 'heyMyRealFirstName'

        self.assertEqual(self.valid_user.first_name, User.objects.get(pk=self.valid_user.pk).first_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'first_name': fake_first_name,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(patched_user.first_name, fake_first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_not_update_first_name_given_invalid_first_name(self):
        fake_first_name = '+++**&&&'

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'first_name': fake_first_name,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertNotEqual(patched_user.first_name, fake_first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_update_last_name_given_last_name(self):
        fake_last_name = 'heyMyRealLastName'

        self.assertEqual(self.valid_user.last_name, User.objects.get(pk=self.valid_user.pk).last_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': fake_last_name,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(patched_user.last_name, fake_last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_update_last_name_given_last_name(self):
        fake_last_name = '++**&&'

        self.assertEqual(self.valid_user.last_name, User.objects.get(pk=self.valid_user.pk).last_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': fake_last_name,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertNotEqual(patched_user.last_name, fake_last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_update_picture_given_valid_picture(self):
        pre_patched_user = User.objects.get(pk=self.valid_user.pk)
        self.assertFalse(pre_patched_user.picture)

        request = APIRequestFactory().patch(
            'api/users/', 
            encode_multipart(boundary=BOUNDARY, data={
                'picture': self.image_file1,
                'confirm_picture': self.image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Token {self.auth_token}"
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(patched_user.picture)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        return
    
    def test_patch_should_not_update_picture_given_invalid_picture(self):
        ten_mb_limit = (1024 * 1024 * 10)
        pre_patched_user = User.objects.get(pk=self.valid_user.pk)
        self.assertFalse(pre_patched_user.picture)

        with TemporaryFile() as temp_file:
            temp_file.seek(ten_mb_limit)
            temp_file.write(b'0')

            request = APIRequestFactory().patch(
                'api/users/', 
                encode_multipart(boundary=BOUNDARY, data={'picture': temp_file}),
                content_type=MULTIPART_CONTENT,
                HTTP_AUTHORIZATION=f"Token {self.auth_token}"
            )
            response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
            patched_user = User.objects.get(pk=self.valid_user.pk)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(patched_user.picture)
            self.assertEqual(self.valid_user.email, patched_user.email)
            self.assertEqual(self.valid_user.username, patched_user.username)
            self.assertEqual(self.valid_user.first_name, patched_user.first_name)
            self.assertEqual(self.valid_user.last_name, patched_user.last_name)
            self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        return

    def test_patch_should_update_latitude_given_valid_latitude(self):
        new_latitude = 1.0

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'latitude': new_latitude,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertEqual(patched_user.latitude, new_latitude)
        return
    
    def test_patch_should_update_longitude_given_valid_longitude(self):
        new_longitude = 1.0

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'longitude': new_longitude,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertEqual(patched_user.longitude, new_longitude)
        return

    def test_patch_should_update_keywords_given_valid_keywords(self):
        new_keywords = ['These', 'Are', 'Test', 'Keywords', 'People']
        lowercased_new_keywords = [keyword.lower() for keyword in new_keywords]

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'keywords': new_keywords,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(patched_user.keywords, lowercased_new_keywords)
        return

class MatchingPhoneNumbersViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            latitude=0,
            longitude=0,
            phone_number="+11234567890")
        self.user1.set_password('randomPassword')
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User.objects.create(
            email="email2@usc.edu",
            username="unrelatedUsername2",
            first_name="completelyDifferentFirstName2",
            last_name="notTheSameLastName2",
            date_of_birth=date(2000, 1, 1),
            latitude=0,
            longitude=0,
            phone_number="+11234567891")
        self.user2.set_password('randomPassword')
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User.objects.create(
            email="email3@usc.edu",
            username="unrelatedUsername3",
            first_name="completelyDifferentFirstName3",
            last_name="notTheSameLastName3",
            date_of_birth=date(2000, 1, 1),
            latitude=100,
            longitude=100,
            phone_number="+11234567892")
        self.user3.set_password('randomPassword')
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)
        return
            
    def test_get_should_return_list_of_matching_users_given_valid_phone_number(self):
        request = APIRequestFactory().post(
            f'api/matching-phone-numbers/',
            {
                'phone_numbers': [str(self.user1.phone_number)]
            },
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)
        response_phonebook = response.data
        expected_phonebook = {str(self.user1.phone_number): ReadOnlyUserSerializer(self.user1).data}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phonebook, expected_phonebook)
        return
    
    def test_get_should_return_list_of_matching_users_given_valid_phone_numbers(self):
        request = APIRequestFactory().post(
            f'api/matching-phone-numbers/',
            {
                'phone_numbers': [
                    str(self.user1.phone_number),
                    str(self.user2.phone_number),
                ]
            },
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}",
        )
        response = MatchingPhoneNumbersView.as_view()(request)
        response_phonebook = response.data
        expected_phonebook = {
            str(self.user1.phone_number): ReadOnlyUserSerializer(self.user1).data,
            str(self.user2.phone_number): ReadOnlyUserSerializer(self.user2).data
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phonebook, expected_phonebook)
        return
    
    def test_get_should_return_list_of_matching_users_given_valid_phone_number_and_invalid_phone_number(self):
        request = APIRequestFactory().post(
            f'api/matching-phone-numbers/',
            {
                'phone_numbers': [
                    str(self.user1.phone_number),
                    'invalidNumber',
                ]
            },
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)
        response_phonebook = response.data
        expected_phonebook = {
            str(self.user1.phone_number): ReadOnlyUserSerializer(self.user1).data,
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phonebook, expected_phonebook)
        return
    
    def test_get_should_not_return_list_given_no_phone_number(self):
        request = APIRequestFactory().post(
            'api/matching-phone-numbers/',
            {
                'phone_numbers': [],
            },
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_get_should_not_return_list_given_no_parameters(self):
        request = APIRequestFactory().post(
            'api/matching-phone-numbers/',
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_get_should_not_return_list_given_nothing(self):
        request = APIRequestFactory().post(
            'api/matching-phone-numbers/',
        )
        response = MatchingPhoneNumbersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

class NearbyUsersViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            latitude=0,
            longitude=0,)
        self.user1.set_password('randomPassword')
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User.objects.create(
            email="email2@usc.edu",
            username="unrelatedUsername2",
            first_name="completelyDifferentFirstName2",
            last_name="notTheSameLastName2",
            date_of_birth=date(2000, 1, 1),
            latitude=0,
            longitude=0,)
        self.user2.set_password('randomPassword')
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.user3 = User.objects.create(
            email="email3@usc.edu",
            username="unrelatedUsername3",
            first_name="completelyDifferentFirstName3",
            last_name="notTheSameLastName3",
            date_of_birth=date(2000, 1, 1),
            latitude=100,
            longitude=100,)
        self.user3.set_password('randomPassword')
        self.user3.save()
        self.auth_token3 = Token.objects.create(user=self.user3)
        return

    def test_get_should_not_return_given_no_auth_user(self):
        request = APIRequestFactory().get(
            'api/nearby-users/',
        )
        response = NearbyUsersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

    def test_get_should_return_only_nearby_users(self):
        serialized_users = [
            ReadOnlyUserSerializer(self.user1).data,
            ReadOnlyUserSerializer(self.user2).data,
        ]

        request = APIRequestFactory().get(
            'api/nearby-users/',
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = NearbyUsersView.as_view()(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response_users, serialized_users)
        return

class RequestPasswordResetViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.user1.set_password('randomPassword')
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

    def test_post_should_not_create_request_given_invalid_email(self):
        fake_email = 'nonexistentEmail@doesNotExist.com'

        request = APIRequestFactory().post(
            'api/request-reset-password/',
            {
                'email': fake_email
            },
        )
        response = RequestPasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PasswordReset.objects.filter(email=fake_email))
        self.assertFalse(mail.outbox)
        return

    def test_post_should_create_request_given_valid_email(self):
        valid_email = self.user1.email

        request = APIRequestFactory().post(
            'api/request-reset-password/',
            {
                'email': valid_email
            },
        )
        response = RequestPasswordResetView.as_view()(request)
        password_reset_requests = PasswordReset.objects.filter(email=valid_email)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(password_reset_requests)
        self.assertTrue(mail.outbox)
        self.assertEqual(mail.outbox[0].to[0], valid_email.lower())
        self.assertTrue(mail.outbox[0].body.find(str(password_reset_requests[0].code)))
        return

class ValidatePasswordResetViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.user1.set_password('randomPassword')
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)
        self.unvalidated_reset_request = PasswordReset.objects.create(email=self.user1.email)
    
    def test_post_should_not_validate_given_invalid_email(self):
        invalid_email = "thisWillNeverEverBeAValidEmail@invalidEmail.net"

        request = APIRequestFactory().post(
            'api/validate-reset-password/',
            {
                'email': invalid_email,
                'code': self.unvalidated_reset_request.code,
            },
        )
        response = ValidatePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PasswordReset.objects.get(email=self.user1.email).validated)
        return

    def test_post_should_not_validate_given_invalid_code(self):
        ten_minutes = datetime.now().timestamp()
        self.unvalidated_reset_request.code_time -= ten_minutes
        self.unvalidated_reset_request.save()

        request = APIRequestFactory().post(
            'api/validate-reset-password/',
            {
                'email': self.unvalidated_reset_request.email,
                'code': self.unvalidated_reset_request.code,
            },
        )
        response = ValidatePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PasswordReset.objects.get(email=self.user1.email).validated)
        return
    
    def test_post_should_not_validate_given_expired_code(self):
        invalid_code = "thisWillNeverEverBeAValidCode"

        request = APIRequestFactory().post(
            'api/validate-reset-password/',
            {
                'email': self.unvalidated_reset_request.email,
                'code': invalid_code,
            },
        )
        response = ValidatePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PasswordReset.objects.get(email=self.user1.email).validated)
        return
    
    def test_post_should_validate_given_valid_code_and_valid_email(self):
        request = APIRequestFactory().post(
            'api/validate-reset-password/',
            {
                'email': self.unvalidated_reset_request.email,
                'code': self.unvalidated_reset_request.code,
            },
        )
        response = ValidatePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordReset.objects.get(email=self.user1.email).validated)
        return

class FinalizePasswordResetViewTest(TestCase):
    def setUp(self):
        self.old_password = 'randomPassword'
        self.new_strong_password = 'newPassword@3312$5'
        self.new_weak_password = '123'

        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.user1.set_password(self.old_password)
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.unvalidated_reset_request = PasswordReset.objects.create(email=self.user1.email)
        
    def test_post_should_not_finalize_given_nonexistent_email_and_strong_password(self):
        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': 'thisEmailDoesNotExist@invalidEmail.net',
                'password': self.new_strong_password,
            },
        )
        response = FinalizePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user1.check_password(self.new_strong_password))
        self.assertTrue(self.user1.check_password(self.old_password))
        return
    
    def test_post_should_not_finalize_given_unvalidated_email_and_strong_password(self):
        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': self.unvalidated_reset_request.email,
                'password': self.new_strong_password,
            },
        )
        response = FinalizePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user1.check_password(self.new_strong_password))
        self.assertTrue(self.user1.check_password(self.old_password))
        return
    
    def test_post_should_not_finalize_given_valid_email_and_empty_password(self):
        reset_request = self.unvalidated_reset_request
        reset_request.validated = True
        reset_request.validation_time = datetime.now().timestamp()
        reset_request.save()

        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': reset_request.email,
                'password': '',
            },
        )
        response = FinalizePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user1.check_password(self.old_password))
        return
    
    def test_post_should_not_finalize_given_valid_email_and_weak_password(self):
        reset_request = self.unvalidated_reset_request
        reset_request.validated = True
        reset_request.validation_time = datetime.now().timestamp()
        reset_request.save()

        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': reset_request.email,
                'password': self.new_weak_password,
            },
        )
        response = FinalizePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user1.check_password(self.new_weak_password))
        self.assertTrue(self.user1.check_password(self.old_password))
        return

    def test_post_should_not_finalize_given_expired_validation_and_strong_password(self):
        ten_minutes = datetime.now().timestamp()

        reset_request = self.unvalidated_reset_request
        reset_request.validated = True
        reset_request.validation_time = datetime.now().timestamp() - ten_minutes
        reset_request.save()

        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': reset_request.email,
                'password': self.new_strong_password,
            },
        )
        response = FinalizePasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user1.check_password(self.new_strong_password))
        self.assertTrue(self.user1.check_password(self.old_password))
        return
    
    def test_post_should_finalize_given_valid_email_and_strong_password(self):
        reset_request = self.unvalidated_reset_request
        reset_request.validated = True
        reset_request.validation_time = datetime.now().timestamp()
        reset_request.save()

        request = APIRequestFactory().post(
            'api/finalize-reset-password/',
            {
                'email': reset_request.email,
                'password': self.new_strong_password,
            },
        )
        response = FinalizePasswordResetView.as_view()(request)
        requesting_user = User.objects.get(email=reset_request.email)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(requesting_user.check_password(self.new_strong_password))
        self.assertFalse(requesting_user.check_password(self.old_password))
        return

# Phone Numbers
class RegisterPhoneNumberViewTest(TestCase):
    def setUp(self):
        TwillioTestClientMessages.created = []

        self.strong_password = 'newPassword@3312$5'
        self.unused_email = "notUsedEmail@usc.edu"

        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1), 
            phone_number="+1234567899")
        self.user1.set_password(self.strong_password)
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)
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

class RequestLoginCodeViewTest(TestCase):
    # phone number
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

        self.user1 = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1),
            phone_number="+12345678999"
        )
        
        PhoneNumberAuthentication.objects.create(
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
                'code': '123456',
            },
        )
        response = ValidateLoginCodeView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return

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