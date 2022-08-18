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
from .models import PasswordReset, PhoneNumberAuthentication, PhoneNumberReset, User, EmailAuthentication

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
        self.fake_password = 'FakeTestingPassword@3124587'
        self.fake_first_name = 'FirstNameOfFakeUser'
        self.fake_last_name = 'LastNameOfFakeUser'
        self.fake_date_of_birth = date(2000, 1, 1)

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
                'password': self.fake_password,
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
        return

    def test_post_should_not_create_user_given_unvalidated_email(self):
        request = APIRequestFactory().post(
            'api/users/',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'phone_number': self.phone_auth.phone_number,
                'username': self.fake_username,
                'password': self.fake_password,
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
                'password': self.fake_password,
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
                'password': self.fake_password,
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
                'password': self.fake_password,
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
                'password': self.fake_password,
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
    
    def test_patch_should_update_password_given_valid_password(self):
        fake_new_password = 'anotherStrongPass@9703$'

        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=fake_new_password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        
        request = APIRequestFactory().patch(
            'api/users/',
            {
                'password': fake_new_password,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=fake_new_password))
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_not_update_password_given_weak_password(self):
        weak_password = '123'

        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=weak_password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'password': weak_password,
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        patched_user = User.objects.get(pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=weak_password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        self.assertEqual(self.valid_user.email, patched_user.email)
        self.assertEqual(self.valid_user.username, patched_user.username)
        self.assertTrue(patched_user.check_password(self.password))
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_not_update_first_name_given_first_name(self):
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
        self.assertEqual(self.valid_user.first_name, patched_user.first_name)
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
        self.assertEqual(self.valid_user.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_not_update_last_name_given_last_name(self):
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
        self.assertEqual(self.valid_user.last_name, patched_user.last_name)
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

    def test_get_with_weird_adam_test(self):
        numbers = ["+16152324830", "+16158404139", "+17145487104", "+16154999956", "+16156063310", "+19495454993", "+19512955360", "+17145664757", "+14246349063", "+15137061654", "+19253234496", "+14046806853", "+16157727706", "+16504923242", "+16154786454", "+16155853509", "+16156362228", "+17748887449", "+19047148117", "+14049335534", "+16158812564", "+12488605998", "+19312426341", "+13146198603", "+16152606214", "+17144500264", "+19144679159", "+16153101645", "+12604371817", "+16153778009", "+16154999757", "+16019510088", "+12137404321", "+15015906344", "+16293950666", "+16154765385", "+12134258698", "+14056417097", "+16154105488", "+16156782781", "+12405780443", "+16159355040", "+16168890857", "+13019800371", "+16159799019", "+16292552077", "+12137406000", "+16159792009", "+16156782781", "+19258191015", "+16159676352", "+18584727726", "+16159451239", "+14023219675", "+16157728904", "+16159578606", "+16155224495", "+12032319237", "+16158780383", "+16154877902", "+18182929114", "+16153069189", "+16155458965", "+16155001525", "+19152048583", "+12158179186", "+16158107915", "+16159444803", "+16155859115", "+12402171606", "+16158387667", "+16154177297", "+17707781015", "+16155213027", "+16156006237", "+16096137106", "+16153064124", "+16158927615", "+16155215668", "+19312197694", "+18032433839", "+16158303302", "+17602192017", "+16157670583", "+19045994751", "+19162127424", "+19497059991", "+16155097056", "+16159395254", "+16155070012", "+16159731520", "+16159466902", "+16503914791", "+16159464212", "+16156241266", "+19042956203", "+16025109191", "+16154171988", "+18056039976", "+16153352314", "+13035137606", "+18157217197", "+18012340941", "+16157880879", "+15024892855", "+16304502322", "+16156932513", "+16157082797", "+16199904879", "+15035772916", "+16153196122", "+16154302081", "+16612106025", "+16157678994", "+16152324831", "+639175361470", "+60138984071", "+821033825740", "+85297234944", "+31648796988", "+819043949525", "+60168283880", "+16159693160", "+16292552077", "+16293950666", "+19312426341", "+16153778009", "+17078492806", "+16153069189", "+16156063310", "+19528185135", "+16153106698", "+16152324830", "+17077977406", "+16153352715", "+19548011239", "+16153645084", "+15135356643", "+16156638005", "+16156361994", "+19256058175", "+821065561057", "+19736923320", "+16152683052", "+12132209306", "+12134074322", "+12134074262", "+12135454764", "+12132488466", "+12133935964", "+12135454774", "+16107512071", "+821040698249", "+19258992887", "+8613699228378", "+16153105700", "+17182881779", "+15415566830", "+16158708848", "+13104977003", "+19496778034", "+18032396839", "+16154197222", "+16154237480", "+16155841314", "+16154140391", "+16158105128", "+14242028828", "+16154782074", "+16158060995", "+16154240533", "+16159751518", "+14408217765", "+18655840962", "+16157124305", "+17042775013", "+15402309074", "+17729990514", "+16788002966", "+19782702428", "+17147951881", "+14136252160", "+18189260248", "+13019229873", "+16157349570", "+19496775137", "+19157108525", "+17038010695", "+12158503525", "+16155006375", "+15736459854", "+18475329491", "+16155044837", "+13233489982", "+15038198335", "+16158405403", "+16156304917", "+15163053031", "+19168041542", "+12403082059", "+17039439961", "+15132925294", "+18435182633", "+13232666228", "+12138800856", "+17022507193", "+16097899792", "+15039359777", "+13016935513", "+14102944474", "+17247179780", "+19083768244", "+16462586898", "+18609665108", "+19172080460", "+18563439995", "+17193576074", "+12157764174", "+14435407885", "+19085917612", "+13013108782", "+12136638513", "+12135454761", "+12137404646", "+16159471135", "+16612055130", "+19097171605", "+16157501007", "+18558286826", "+15622545158", "+12678257019", "+12137404321", "+12137406000", "+12136638513", "+12137647904", "+16152934880", "+16507438526", "+15599066050", "+12105590176", "+12135739722", "+12135454761", "+15053316541", "+12133359899", "+16039306369", "+19259896741", "+15103580221", "+17633506119", "+12135514191", "+17205568641", "+19493552820", "+17029848340", "+15109284710", "+16366712511", "+19736151760", "+19096366853", "+14255999252", "+19143349947", "+16124080666", "+14255053630", "+17733978177", "+19182303723", "+19092259383", "+19099049712", "+12134487450", "+15136309382", "+19514541419", "+13108029280", "+15713957207", "+16786436407", "+17138537781", "+18049387370", "+14088345059", "+17143430706", "+19496132474", "+17863665979", "+15109246143", "+12105590176", "+12135739722", "+16265347618", "+15039986083", "+12137409355", "+14054768936", "+16262438458", "+16174071281", "+19517644497", "+12137136344", "+19496486945", "+13108741292", "+14255996945", "+12132596001", "+14085102914", "+14084972903", "+14247449169", "+14088008249", "+14088130792", "+14088059406", "+16692568020", "+12135445735", "+15106763739", "+18086907274", "+13109033003", "+16266882454", "+18302202888", "+15623387849", "+15184615537", "+16025712781", "+18475338845", "+18187958826", "+19515264309", "+19729630554", "+18587767882", "+12135739691", "+12135513016", "+19188517220", "+15207301541", "+19255498696", "+14029578405", "+19097039796", "+12016009035", "+17249000219", "+15105900151", "+12135514805", "+16519559869", "+13234498345", "+14083916347", "+13236460181", "+16504525608", "+19255231295", "+13108637363", "+19522170997", "+16782947719", "+16612892011", "+19092700503", "+15623932595", "+16466296335", "+13108424811", "+14152992953", "+17148588616", "+12132040003", "+17028583111", "+12133789072", "+12034437340", "+14126279900", "+19496003045", "+14124525074", "+18319157309", "+19712807249", "+16508683360", "+17752291224", "+17206261394", "+13132714523", "+18022306893", "+18184162467", "+15038572137", "+13232539131", "+19727862001", "+13103438777", "+12138060422", "+16509429492", "+13239482526", "+12013556275", "+13035964333", "+12133730090", "+16506566757", "+15136028241", "+12137402924", "+13104095013", "+13313189920", "+16094772073", "+14234637381", "+19492806844", "+13146055638", "+17144713748", "+13196544698", "+12137404444", "+12137404077", "+13363385704", "+16319027404", "+13104672634", "+13393641189", "+15209870612", "+16505189682", "+13108953606", "+16264744102", "+12028200150", "+18286651291", "+12132758836", "+16262659869", "+14255126622", "+13107558868", "+13107966367", "+12137400472", "+12148029798", "+18057103297", "+15102034279", "+12137095504", "+13123074316", "+16142145758", "+14106246759", "+14066009813", "+12133348651", "+14083683191", "+17187109998", "+16692426824", "+13234209633", "+13106623745", "+15105082102", "+18583348580", "+12142120795", "+16617037037", "+12132846938", "+12136634785", "+16463428783", "+14089130326", "+14158128951", "+17608838919", "+12134791625", "+12137400427", "+16153223246", "+16153228303", "+16153434788", "+13109803088", "+16506567344", "+13014732179", "+18179079363", "+12622907327", "+12144713327", "+13233694137", "+17029081836", "+19132841568", "+12153817279", "+18587330184", "+13107396306", "+12488905656", "+17173509499", "+15628797722", "+17154415652", "+16465410907", "+12165331397", "+12135278846", "+13238165048", "+18102297628", "+14102795198", "+16153202908", "+16307039114", "+16504714720", "+16154832013", "+16158868200", "+12815078072", "+16159240200", "+16159252345", "+15024892855", "+16262036149", "+12819083700", "+12017550054", "+16195738735", "+16159830667", "+16152606377", "+12135037451", "+16159693160", "+17857387852", "+16159671773", "+19495339222", "+16156939186", "+16159670922", "+16154834302", "+16304845140", "+12406766859", "+15419688722", "+16154384836", "+16154232815", "+16155744976", "+16156302512", "+16156008535", "+12132688969", "+60132887488", "+14076704407", "+16159725030", "+16159754713", "+16155841950", "+16158815643", "+16507998532", "+19162309938", "+19316988144", "+16156364514", "+16155043045", "+16154002081", "+16157884728", "+17638079637", "+16154069491", "+13058781710", "+16159394668", "+16159754270", "+16159399222", "+16155228574", "+16157191092", "+16154806215", "+13172012437", "+16038514594", "+16155459722", "+16155032960", "+16153646048", "+16158561685", "+16157079039", "+16157718800", "+16152930997", "+12243924845", "+16153396797", "+19495479604", "+16152606143", "+16158667816", "+18284582814", "+16159177323", "+16154786969", "+17074861549", "+19084897782", "+16159480313", "+16156276040", "+19292865331", "+16154918241", "+16154992377", "+17202776574", "+15623436832", "+16159247388", "+16153731012", "+16155000676", "+16159756640", "+17045939777", "+12038309258", "+16159990222", "+15085798750", "+60164461982", "+16155165114", "+16152180595", "+16157392779", "+12483425637", "+16366983429", "+16154919762", "+14085050755", "+19086255321", "+16159398989", "+16154197222", "+15059181278", "+19179697937", "+16157272977", "+13108976115", "+16158918058", "+19893079044", "+14055090325", "+16158668437", "+17739431511", "+16154383890", "+16477705695", "+16155737747", "+14045478224", "+16159698413", "+14435146060", "+12035399787", "+13236522422", "+16159792285", "+16159392407", "+19255963758", "+17044910473", "+16156039110", "+14155711200", "+16159623999", "+16155847719", "+16156016498", "+14157179784", "+16159275988", "+16159736909", "+16159132030", "+16158402435", "+16158794057", "+18057290381", "+16159265696", "+16154381242", "+13059685892", "+16157617470", "+19176791689", "+19376572657", "+16159446656", "+16785459233", "+19255776734", "+14158619483", "+19493510168", "+13108496623", "+16155548985", "+13139714933", "+19257194074", "+16155949567", "+16362366796", "+16154837563", "+12132551488", "+16157209966", "+16155000065", "+12145774977", "+16159069963", "+16159694711", "+14693076531", "+15174202358", "+14057615545", "+639178492902", "+12149343178", "+18304311547", "+16154400407", "+16158795779", "+16154827227", "+16153644248", "+16158061815", "+16152003648", "+18479099678", "+19377011965", "+18184551376", "+19182609192", "+16159999558", "+16158708445", "+16154198851", "+15136421936", "+16159621528", "+13236464399", "+14155336063", "+16154743299", "+16154155209", "+16159202134", "+17743033604", "+19733031653", "+17857641142", "+16153366732", "+639154103560", "+16158188011", "+16155212171", "+19316397004", "+16158566256", "+15714421687", "+13102280846", "+12026950266", "+16153104548", "+16159249518", "+16159255980", "+18126294144", "+18058684128", "+16157071906", "+16159756090", "+16158529349", "+13128904342", "+16308859331", "+16159278002", "+12032337351", "+13109631339", "+16156938358", "+13109076354", "+16159754714", "+16158920707", "+16155744820", "+16158784980", "+16159757357", "+12052005355", "+15619083651", "+19135968983", "+16159675717", "+16153366935", "+12016753899", "+16617132110", "+14806770112", "+16158786089", "+19139577730", "+16152183602", "+13477985699", "+16158294373", "+16159201458", "+15612897199", "+16159550685", "+17743070969", "+19312470811", "+16143591532", "+16156006998", "+18659632209", "+16158046934", "+16156137402", "+16158783888", "+16155744401", "+15043529245", "+17737440260", "+13235942653", "+16309158836", "+17738167035", "+16154205505", "+16158788759", "+19732226525", "+16156006921", "+16178340821", "+19178739423", "+12132538886", "+16159727656", "+14259854079", "+14237186308", "+16158790194", "+18054519016", "+18165857343", "+18188585762", "+16158567321", "+14088864443", "+16153372344", "+16312410594", "+16159245383", "+16158565405", "+16156183799", "+16159203371", "+16153487600", "+19495178599", "+16158918894", "+16156688918", "+16154841897", "+16154400072", "+60138300581", "+16502243880", "+13177307748", "+16156186552", "+16159642353", "+16159793676", "+12069539765", "+16159441448", "+16154577472", "+16153324640", "+16156136759", "+16154176124", "+16156892400", "+447923886526", "+16158783845", "+12624436535", "+16154273660", "+19258181843", "+19092476022", "+16154796492", "+17179993993", "+16263429978", "+15105796056", "+16158707938", "+16158875513", "+19175147111", "+14048042977", "+16156020250", "+16155577408", "+16367959009", "+13109389180", "+16158403492", "+18434129160", "+16157728097", "+16158157905", "+16159753063", "+12532544564", "+16159340244", "+16154724800", "+18563132554", "+16158868765", "+16105509203", "+13194008619", "+13035904858", "+12142265455", "+12532692799", "+17193146487", "+16157072560", "+16507849275", "+13016761185", "+17146838695", "+15403276159", "+16154197067", "+17608893262", "+16158934896", "+14106931209", "+13522225230", "+16159735389", "+16157537942", "+16154959736", "+13059349316", "+16126691730", "+17724041727", "+16154960142", "+16316786347", "+16155854190", "+16159390426", "+16157128313", "+18186365714", "+16153514495", "+16156890969", "+16154963306", "+16159160131", "+16157723337", "+19254281643", "+16159737705", "+14252196896", "+18139242234", "+16154990913", "+16156893884", "+12036151418", "+19148449108", "+14054205925", "+16155828764", "+16157723337", "+19317975036", "+13149151995", "+16152602422", "+16159752707", "+16155458965", "+16158793002", "+16158122761", "+5521984690915"]
        query_params = []
        for number in numbers:
            query_params.append(f"phone_numbers={number}")
        url_formatted_params = "?" + "&".join(query_params)
        url = f'api/matching-phone-numbers/{url_formatted_params}'

        request = APIRequestFactory().get(
            url,
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)
        response_phonebook = response.data
        print(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
    def test_get_should_return_list_of_matching_users_given_valid_phone_number(self):
        request = APIRequestFactory().get(
            f'api/matching-phone-numbers-users/?phone_numbers={str(self.user1.phone_number)}',
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)
        response_phonebook = response.data
        expected_phonebook = {str(self.user1.phone_number): ReadOnlyUserSerializer(self.user1).data}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phonebook, expected_phonebook)
        return
    
    def test_get_should_return_list_of_matching_users_given_valid_phone_numbers(self):
        request = APIRequestFactory().get(
            f'api/matching-phone-numbers-users/ \
            ?phone_numbers={str(self.user1.phone_number)}&phone_numbers={str(self.user2.phone_number)}',
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
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
        request = APIRequestFactory().get(
            f'api/matching-phone-numbers-users/ \
            ?phone_numbers={str(self.user1.phone_number)}&phone_numbers=invalidNumber',
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
    
    def test_get_should_return_empty_list_given_no_phone_number(self):
        request = APIRequestFactory().get(
            'api/matching-phone-numbers-users/',
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = MatchingPhoneNumbersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return
    
    def test_get_should_not_return_list_given_nothing(self):
        request = APIRequestFactory().get(
            'api/matching-phone-numbers-users/',
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