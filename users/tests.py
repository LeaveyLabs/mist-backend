from datetime import datetime
from django.core import mail, cache
from django.forms import ValidationError
from django.test import TestCase
from django.contrib.auth import authenticate
from users.models import User
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, force_authenticate
from .serializers import CompleteUserSerializer, ReadOnlyUserSerializer
from .views import RegisterUserEmailView, UserView, ValidateUserEmailView
from .models import User, EmailAuthentication

# Create your tests here.
class ThrottleTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)

    def test_throttle_anonymous_user_above_50_calls(self):
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

        self.assertEquals(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        return
        
    def test_do_not_throttle_anonymous_user_at_or_below_50_calls(self):
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

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        return

    def test_throttle_authenticated_user_above_100_calls(self):
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
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = RegisterUserEmailView.as_view()(request)

        self.assertEquals(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        return

    def test_do_not_throttle_authenticated_user_at_or_below_100_calls(self):
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
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = RegisterUserEmailView.as_view()(request)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
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
            )
            force_authenticate(fake_request, user=self.valid_user, token=self.auth_token)
            fake_response = RegisterUserEmailView.as_view()(fake_request)
        

class RegisterUserEmailViewTest(TestCase):
    def setUp(self):
        cache.cache.clear()

    def test_register_user_valid_email(self):
        self.assertFalse(EmailAuthentication.objects.filter(
            email='RegisterThisFakeEmail@usc.edu'))

        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'RegisterThisFakeEmail@usc.edu',
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)
        email_auths = EmailAuthentication.objects.filter(
            email='RegisterThisFakeEmail@usc.edu')

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(email_auths)
        self.assertTrue(mail.outbox)
        self.assertEquals(mail.outbox[0].to[0], 'RegisterThisFakeEmail@usc.edu')
        self.assertTrue(mail.outbox[0].body.find(str(email_auths[0].code)))
        return
    
    def test_register_user_invalid_email(self):
        request = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'ThisIsAnInvalidEmail',
            },
            format='json',
        )
        response = RegisterUserEmailView.as_view()(request)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.filter(
            email='ThisIsAnInvalidEmail'))
        self.assertFalse(mail.outbox)
        return

class ValidateUserEmailViewTest(TestCase):
    def test_validate_user_valid_code(self):
        registration = EmailAuthentication(
            email='ValidateThisFakeEmail@usc.edu',
        )
        registration.save()

        self.assertFalse(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)

        request = APIRequestFactory().post('api-validate/',
            {
                'email': 'ValidateThisFakeEmail@usc.edu',
                'code': registration.code,
            },
            format='json',
        )
        response = ValidateUserEmailView.as_view()(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)
        return
    
    def test_validate_user_invalid_code(self):
        registration = EmailAuthentication(
            email='ValidateThisFakeEmail@usc.edu',
        )
        registration.save()

        self.assertFalse(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)

        request = APIRequestFactory().post(
            'api-validate/',
            {
                'email': 'ValidateThisFakeEmail@usc.edu',
                'code': int(registration.code)+1,
            },
            format='json',
        )
        response = ValidateUserEmailView.as_view()(request)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)
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

    def test_create_user_valid_email(self):
        self.assertFalse(User.objects.filter(
            email=self.email_auth.email,
            username=self.fake_username,
            password=self.fake_password,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
        ))

        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': self.email_auth.email,
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
            },
            format='json',
        )
        response = UserView.as_view({'post':'create'})(request)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(
            email=self.email_auth.email,
            username=self.fake_username,
            password=self.fake_password,
            first_name=self.fake_first_name,
            last_name=self.fake_last_name,
        ))
        return

    def test_create_user_invalid_email(self):
        request = APIRequestFactory().post(
            'api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username': self.fake_username,
                'password': self.fake_password,
                'first_name': self.fake_first_name,
                'last_name': self.fake_last_name,
            },
            format='json',
        )

        with self.assertRaises(ValidationError):
            UserView.as_view({'post':'create'})(request)
        return

    def test_obtain_token_valid_user(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
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

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        return
    
    def test_obtain_token_invalid_username(self):
        user = User(
            email=self.email_auth.email,
            username=self.fake_username,
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

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return
    
    def test_obtain_token_invalid_password(self):
        user = User(
            email= self.email_auth.email,
            username= self.fake_username,
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
        
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', response.data)
        return

class UserViewGetTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.user_serializer = CompleteUserSerializer(self.valid_user)

    # Serialization
    def test_return_readonly_user_with_nonmatching_token(self):
        non_matching_user = User.objects.create(
            email="nonMatchingEmail@usc.edu",
            username="nonMatchingUsername",
            first_name="thisFirstNameHasNotBeenTaken",
            last_name="thisLastNameHasNotBeenTaken")
        non_matching_user.set_password('nonMatchingPassword')
        non_matching_user.save()
        auth_token = Token.objects.create(user=non_matching_user)

        user_serializer = ReadOnlyUserSerializer(self.valid_user)

        request = APIRequestFactory().get(
            'api/users/',
            format='json',
        )
        force_authenticate(request, user=non_matching_user, token=auth_token)
        response = UserView.as_view({'get':'retrieve'})(request, pk=self.valid_user.id)
        print(response.data, user_serializer.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, user_serializer.data)
        return
    
    def test_return_full_user_with_matching_token(self):
        request = APIRequestFactory().get(
            'api/users/',
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'retrieve'})(request, pk=self.valid_user.id)
        response_user = response.data
        
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response_user, self.user_serializer.data)
        return

    # Valid Queries
    def test_get_user_by_valid_text(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'name',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return

    def test_get_user_by_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelatedUsername',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return
    
    def test_get_user_by_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelated',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return

    def test_get_user_by_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completelyDifferentFirstName',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return
    
    def test_get_user_by_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completely',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return

    def test_get_user_by_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSameLastName',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return
        
    def test_get_user_by_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSame',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data[0], self.user_serializer.data)
        return

    def test_get_user_by_valid_token(self):
        serialized_users = [self.user_serializer.data]

        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': self.auth_token,
            },
            format='json',
        )

        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response_users, serialized_users)
        return

    # Invalid User
    def test_get_user_by_invalid_text(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'notInTheTextAtAll',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return

    def test_get_user_by_invalid_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'thisUsernameDoesNotExist',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_get_user_by_invalid_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'sername',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return

    def test_get_user_by_invalid_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'thisFirstNameDoesNotExist',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return
    
    def test_get_user_by_invalid_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'DifferentFirstName',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return

    def test_get_user_by_invalid_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'thisLastNameDoesNotExist',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return

    def test_get_user_by_invalid_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'astName',
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'get':'list'})(request)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)        
        return
    
    def test_get_user_by_invalid_token(self):
        invalid_token = "InvalidToken"
        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': invalid_token,
            },
            format='json',
        )

        force_authenticate(request, user=self.valid_user, token=invalid_token)
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data
        
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

class UserViewDeleteTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.unused_pk = 151

    def test_delete_valid_user(self):
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))

        request = APIRequestFactory().delete('api/users/')
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.valid_user.pk))
        return

    def test_delete_invalid_user(self):
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))

        request = APIRequestFactory().delete('api/users/')
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.unused_pk)

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.valid_user.pk))
        return

class UserViewPatchTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.password = "strongPassword@1354689$"
        self.valid_user.set_password(self.password)
        self.valid_user.save()
        self.auth_token = Token.objects.create(user=self.valid_user)
        self.unused_pk = 151

    def test_patch_invalid_user(self):
        self.assertFalse(User.objects.filter(pk=self.unused_pk))

        request = APIRequestFactory().patch('api/users/')
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.unused_pk)

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(User.objects.filter(pk=self.unused_pk))
        return
        
    def test_patch_valid_username(self):
        self.assertEquals(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)
        fake_new_username = 'FakeNewUsername'

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': fake_new_username,
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)
        
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(fake_new_username, User.objects.get(pk=self.valid_user.pk).username)
        return
    
    def test_patch_invalid_username(self):
        self.assertEquals(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': "",
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(self.valid_user.username, User.objects.get(pk=self.valid_user.pk).username)
        return
    
    def test_patch_valid_password(self):
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
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=fake_new_password))
        return
    
    def test_patch_invalid_password(self):
        fake_new_password = '123'

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
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=fake_new_password))
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password=self.password))
        return

    def test_patch_first_name(self):
        fake_first_name = 'heyMyRealFirstName'

        self.assertEquals(self.valid_user.first_name, User.objects.get(pk=self.valid_user.pk).first_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'first_name': fake_first_name,
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(fake_first_name, User.objects.get(pk=self.valid_user.pk).first_name)
        return
    
    def test_patch_last_name(self):
        fake_last_name = 'heyMyRealLastName'

        self.assertEquals(self.valid_user.last_name, User.objects.get(pk=self.valid_user.pk).last_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': fake_last_name,
            },
            format='json',
        )
        force_authenticate(request, user=self.valid_user, token=self.auth_token)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.valid_user.pk)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(fake_last_name, User.objects.get(pk=self.valid_user.pk).last_name)
        return