from datetime import date, datetime, timedelta
from tempfile import TemporaryFile
from django.core import mail, cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from django.contrib.auth import authenticate
from users.models import User
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from .serializers import CompleteUserSerializer, ReadOnlyUserSerializer
from .views import FinalizePasswordResetView, RegisterUserEmailView, RequestPasswordResetView, UserView, ValidatePasswordResetView, ValidateUserEmailView, ValidateUsernameView
from .models import PasswordReset, User, EmailAuthentication

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

    def test_should_throttle_authenticated_user_above_100_calls(self):
        number_of_calls = 100
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

    def test_should_not_throttle_authenticated_user_at_or_below_100_calls(self):
        number_of_calls = 99
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

class UserViewPostTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.email_auth = EmailAuthentication.objects.create(
            email='thisEmailDoesExist@usc.edu',
        )
        self.email_auth.validated = True
        self.email_auth.validation_time = datetime.now().timestamp()
        self.email_auth.save()

        self.fake_username = 'FakeTestingUsername'
        self.fake_password = 'FakeTestingPassword@3124587'
        self.fake_first_name = 'FirstNameOfFakeUser'
        self.fake_last_name = 'LastNameOfFakeUser'
        self.fake_date_of_birth = date(2000, 1, 1)

    def test_post_should_create_user_given_validated_email(self):
        self.assertFalse(User.objects.filter(
            email=self.email_auth.email,
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))

        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': self.email_auth.email,
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
            },
            format='json',
        )
        response = UserView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(
            email=self.email_auth.email,
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))
        return

    def test_post_should_not_create_user_given_unvalidated_email(self):
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))

        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
            },
            format='json',
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))
        return
    
    def test_post_should_not_create_user_given_expired_validation(self):
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))

        ten_minutes = timedelta(minutes=10).total_seconds()

        self.email_auth.validation_time -= ten_minutes
        self.email_auth.save()

        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': self.fake_date_of_birth,
            },
            format='json',
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
            date_of_birth=self.fake_date_of_birth,
        ))
        return
    
    def test_post_should_not_create_user_given_user_under_age_13(self):
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
        ))

        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
                'date_of_birth': date.today(),
            },
            format='json',
        )
        response = UserView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(
            email='thisEmailDoesNotExist@usc.edu',
            username=self.fake_username,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
        ))
        return

class APITokenViewPostTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.email_auth = EmailAuthentication.objects.create(
            email='thisEmailDoesExist@usc.edu',
        )
        self.email_auth.validated = True
        self.email_auth.validation_time = datetime.now().timestamp()
        self.email_auth.save()

        self.fake_username = 'FakeTestingUsername'
        self.fake_password = 'FakeTestingPassword@3124587'
        self.fake_first_name = 'FirstNameOfFakeUser'
        self.fake_last_name = 'LastNameOfFakeUser'
        
    def test_post_should_obtain_token_given_valid_credentials(self):
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
                'username': self.fake_username, 
                'password': self.fake_password,
            },
            format='json',
        )
        response = obtain_auth_token(request)

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
                'username': 'ThisUserDoesNotExist', 
                'password': self.fake_password,
            },
            format='json',
        )
        response = obtain_auth_token(request)

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
                'username': self.fake_username, 
                'password': 'ThisPasswordDoesNotExist',
            },
            format='json',
        )

        response = obtain_auth_token(request)
        
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
            date_of_birth=date(2000, 1, 1))
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
            date_of_birth=date(2000, 1, 1))
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
    def test_get_should_return_user_given_text(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'name',
            },
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
    def test_get_should_not_return_user_given_nonexistent_text(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'notInTheTextAtAll',
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
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName",
            date_of_birth=date(2000, 1, 1))
        self.password = "strongPassword@1354689$"
        self.valid_user.set_password(self.password)
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.unused_pk = 151

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
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(fake_new_username, User.objects.get(pk=self.valid_user.pk).username)
        return
    
    def test_patch_should_not_update_username_given_invalid_username(self):
        self.assertEqual(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': "",
            },
            format='json',
            HTTP_AUTHORIZATION='Token {}'.format(self.auth_token),
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=fake_new_password))
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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=weak_password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.first_name, User.objects.get(pk=self.valid_user.pk).first_name)
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.valid_user.last_name, User.objects.get(pk=self.valid_user.pk).last_name)
        return

    def test_patch_should_update_picture_given_valid_picture(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image_file = SimpleUploadedFile('small.gif', small_gif, content_type='image/gif')
        self.assertFalse(User.objects.get(pk=self.valid_user.pk).picture)

        request = APIRequestFactory().patch(
            'api/users/', 
            encode_multipart(boundary=BOUNDARY, data={'picture': image_file}),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Token {self.auth_token}"
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(pk=self.valid_user.pk).picture)
        return
    
    def test_patch_should_update_picture_given_invalid_picture(self):
        ten_mb_limit = (1024 * 1024 * 10)
        self.assertFalse(User.objects.get(pk=self.valid_user.pk).picture)

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

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(User.objects.get(pk=self.valid_user.pk).picture)
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