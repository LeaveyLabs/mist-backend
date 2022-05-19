import random
from datetime import datetime
from django.forms import ValidationError
from django.test import TestCase
from django.contrib.auth import authenticate
from users.models import User
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.test import APIRequestFactory, force_authenticate
from .serializers import UserSerializer
from .views import RegisterUserEmailView, UserView, ValidateUserEmailView
from .models import User, EmailAuthentication

# Create your tests here.
class RegisterUserEmailViewTest(TestCase):
    def test_register_user_valid_email(self):
        # insert user to database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous1@usc.edu',
            },
            format='json',
        )
        raw_view = RegisterUserEmailView.as_view()(response)
        # insertion should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_201_CREATED)
        # should be one registration request in the DB
        requests = EmailAuthentication.objects.filter(
            email='anonymous1@usc.edu')
        self.assertEqual(len(requests), 1)
        return
    
    def test_register_user_invalid_email(self):
        # insert user to database
        factory = APIRequestFactory()
        response = factory.post('api-register/',
            {
                'email':'anonymous1',
            },
            format='json',
        )
        raw_view = RegisterUserEmailView.as_view()(response)
        # insertion should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        # should be one registration request in the DB
        requests = EmailAuthentication.objects.filter(
            email='anonymous1')
        self.assertEqual(len(requests), 0)
        return

class ValidateUserEmailViewTest(TestCase):
    def test_validate_user_valid_code(self):
        # registration request
        code = f'{random.randint(0, 999_999):06}'
        registration = EmailAuthentication(
            email='anonymous2@usc.edu',
            code=code,
            code_time=datetime.now().timestamp(),
            validation_time=None,
            validated=False,
        )
        registration.save()
        # test validation
        factory = APIRequestFactory()
        response = factory.post('api-validate/',
            {
                'email':'anonymous2@usc.edu',
                'code':code,
            },
            format='json',
        )
        raw_view = ValidateUserEmailView.as_view()(response)
        # http should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        # registration should be validated
        registration = EmailAuthentication.objects.filter(
            email='anonymous2@usc.edu')[0]
        self.assertTrue(registration.validated)
        return
    
    def test_validate_user_invalid_code(self):
        # registration request
        code = f'{random.randint(0, 999_999):06}'
        registration = EmailAuthentication(
            email='anonymous2@usc.edu',
            code=code,
            code_time=datetime.now().timestamp(),
            validation_time=None,
            validated=False,
        )
        registration.save()
        # test validation
        factory = APIRequestFactory()
        response = factory.post('api-validate/',
            {
                'email':'anonymous2@usc.edu',
                'code':int(code)+1,
            },
            format='json',
        )
        raw_view = ValidateUserEmailView.as_view()(response)
        # http should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        # registration should be validated
        registration = EmailAuthentication.objects.filter(
            email='anonymous2@usc.edu')[0]
        self.assertFalse(registration.validated)
        return

class UserViewPostTest(TestCase):
    def setUp(self):
        self.email_auth = EmailAuthentication.objects.create(
            email='thisEmailDoesExist@usc.edu',
            code=f'{random.randint(0, 999_999):06}',
            code_time=datetime.now().timestamp(),
            validated=True,
            validation_time=datetime.now().timestamp(),
        )

    def test_create_user_valid_email(self):
        factory = APIRequestFactory()
        response = factory.post('api/users/',
            {
                'email': self.email_auth.email,
                'username':'mous2',
                'password':'anon52349',
                'first_name':'anony',
                'last_name':'mous',
            },
            format='json',
        )
        raw_view = UserView.as_view({'post':'create'})(response)
        self.assertEquals(raw_view.status_code, status.HTTP_201_CREATED)
        return

    def test_create_user_invalid_email(self):
        factory = APIRequestFactory()
        response = factory.post('api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username':'mous2',
                'password':'anon52349',
                'first_name':'anony',
                'last_name':'mous',
            },
            format='json',
        )
        with self.assertRaises(ValidationError):
            UserView.as_view({'post':'create'})(response)
        return

    def test_obtain_token_valid_user(self):
        user = User(
            email='anonymous3@usc.edu',
            username='anonymous3',
        )
        user.set_password('fakepass12345')
        user.save()
        # generate auth token
        factory = APIRequestFactory()
        response = factory.post('api-token/',
            {
                'username':'anonymous3', 
                'password':'fakepass12345',
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        # generation should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        return
    
    def test_obtain_token_invalid_user(self):
        # generate auth token
        factory = APIRequestFactory()
        response = factory.post('api-token/',
            {
                'username':'anonymous3', 
                'password':'fakepass12345',
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        # generation should be successful
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        return

class UserViewGetTest(TestCase):
    def setUp(self):
        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.serialized_user = UserSerializer(self.valid_user)

    # Valid Queries
    def test_query_user_by_valid_text(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'text': 'name',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_user_by_valid_full_username(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'username': 'unrelatedUsername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
    
    def test_query_user_by_valid_prefix_username(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'username': 'unrelated',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_valid_user_by_full_first_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'first_name': 'completelyDifferentFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
    
    def test_query_valid_user_by_prefix_first_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'first_name': 'completely',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_valid_user_by_full_last_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'last_name': 'notTheSameLastName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
        
    def test_query_valid_user_by_prefix_last_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'last_name': 'notTheSame',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    # Invalid User
    def test_query_user_by_invalid_text(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'text': 'notInTheTextAtAll',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_username(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'username': 'thisUsernameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return
    
    def test_query_user_by_invalid_prefix_username(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'username': 'sername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_first_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'first_name': 'thisFirstNameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return
    
    def test_query_user_by_invalid_prefix_first_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'first_name': 'DifferentFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_last_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'last_name': 'thisLastNameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_prefix_last_name(self):
        factory = APIRequestFactory()
        response = factory.get('api/users/',
            {
                'last_name': 'astName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

class UserViewDeleteTest(TestCase):
    def setUp(self):
        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password('randomPassword')
        self.valid_user.save()
        self.unused_pk = 151

    def test_delete_valid_user(self):
        factory = APIRequestFactory()
        response = factory.delete('api/users/')
        raw_view = UserView.as_view({'delete':'destroy'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEquals(
            len(User.objects.filter(email=self.valid_user.email)), 0)
        return

    def test_delete_invalid_user(self):
        factory = APIRequestFactory()
        response = factory.delete('api/users/')
        raw_view = UserView.as_view({'delete':'destroy'})(response, pk=self.unused_pk)
        self.assertEquals(raw_view.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(
            len(User.objects.filter(email=self.valid_user.email)), 1)
        return

class UserViewPatchTest(TestCase):
    def setUp(self):
        self.valid_user = User.objects.create(
            email="email@usc.edu",
            username="unrelatedUsername",
            first_name="completelyDifferentFirstName",
            last_name="notTheSameLastName")
        self.valid_user.set_password("strongPassword@1354689$")
        self.valid_user.save()
        self.unused_pk = 151

    def test_patch_invalid_user(self):
        factory = APIRequestFactory()
        response = factory.patch('api/users/')
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.unused_pk)
        self.assertEquals(raw_view.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(self.valid_user, 
        User.objects.get(email=self.valid_user.email))
        return
        
    def test_patch_valid_username(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'username': 'newUsername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals('newUsername', 
        User.objects.get(email=self.valid_user.email).username)
        return
    
    def test_patch_invalid_username(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'username': "",
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_patch_valid_password(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'password': 'anotherStrongPass@9703$',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, password='anotherStrongPass@9703$'))
        return
    
    def test_patch_invalid_password(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'password': '123',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, password=self.valid_user.password))
        return

    def test_patch_first_name(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'first_name': 'heyMyRealFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals(
            'heyMyRealFirstName', 
            User.objects.get(email=self.valid_user.email).first_name)
        return
    
    def test_patch_last_name(self):
        factory = APIRequestFactory()
        response = factory.patch(
            'api/users/',
            {
                'last_name': 'heyMyRealLastName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals(
            'heyMyRealLastName', 
            User.objects.get(email=self.valid_user.email).last_name)
        return