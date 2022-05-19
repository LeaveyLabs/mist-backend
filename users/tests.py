from datetime import datetime
from django.forms import ValidationError
from django.test import TestCase
from django.contrib.auth import authenticate
from users.models import User
from rest_framework import status
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.test import APIRequestFactory
from .serializers import UserSerializer
from .views import RegisterUserEmailView, UserView, ValidateUserEmailView
from .models import User, EmailAuthentication

# Create your tests here.
class RegisterUserEmailViewTest(TestCase):
    def test_register_user_valid_email(self):
        response = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'RegisterThisFakeEmail@usc.edu',
            },
            format='json',
        )

        raw_view = RegisterUserEmailView.as_view()(response)

        self.assertEquals(raw_view.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmailAuthentication.objects.filter(
            email='RegisterThisFakeEmail@usc.edu'))
        return
    
    def test_register_user_invalid_email(self):
        response = APIRequestFactory().post(
            'api-register/',
            {
                'email': 'ThisIsAnInvalidEmail',
            },
            format='json',
        )

        raw_view = RegisterUserEmailView.as_view()(response)

        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.filter(
            email='ThisIsAnInvalidEmail'))
        return

class ValidateUserEmailViewTest(TestCase):
    def test_validate_user_valid_code(self):
        registration = EmailAuthentication(
            email='ValidateThisFakeEmail@usc.edu',
        )
        registration.save()

        response = APIRequestFactory().post('api-validate/',
            {
                'email': 'ValidateThisFakeEmail@usc.edu',
                'code': registration.code,
            },
            format='json',
        )

        raw_view = ValidateUserEmailView.as_view()(response)

        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertTrue(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)
        return
    
    def test_validate_user_invalid_code(self):
        registration = EmailAuthentication(
            email='ValidateThisFakeEmail@usc.edu',
        )
        registration.save()

        response = APIRequestFactory().post(
            'api-validate/',
            {
                'email': 'ValidateThisFakeEmail@usc.edu',
                'code': int(registration.code)+1,
            },
            format='json',
        )

        raw_view = ValidateUserEmailView.as_view()(response)

        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(EmailAuthentication.objects.get(
            email='ValidateThisFakeEmail@usc.edu').validated)
        return

class UserViewPostTest(TestCase):
    def setUp(self):
        self.email_auth = EmailAuthentication.objects.create(
            email='thisEmailDoesExist@usc.edu',
        )
        self.email_auth.validated = True
        self.email_auth.validation_time = datetime.now().timestamp()
        self.email_auth.save()

    def test_create_user_valid_email(self):        
        response = APIRequestFactory().post(
            'api/users/',
            {
                'email': self.email_auth.email,
                'username':'FakeTestingUsername',
                'password':'FakeTestingPassword@3124587',
                'first_name':'FirstNameOfFakeUser',
                'last_name':'LastNameOfFakeUser',
            },
            format='json',
        )

        raw_view = UserView.as_view({'post':'create'})(response)

        self.assertEquals(raw_view.status_code, status.HTTP_201_CREATED)
        return

    def test_create_user_invalid_email(self):
        response = APIRequestFactory().post(
            'api/users/',
            {
                'email': 'thisEmailDoesNotExist@usc.edu',
                'username':'FakeTestingUsername',
                'password':'FakeTestingPassword@3124587',
                'first_name':'FirstNameOfFakeUser',
                'last_name':'LastNameOfFakeUser',
            },
            format='json',
        )
        
        with self.assertRaises(ValidationError):
            UserView.as_view({'post':'create'})(response)
        return

    def test_obtain_token_valid_user(self):
        user = User(
            email= self.email_auth.email,
            username= 'FakeTestingUsername',
        )
        user.set_password('FakeTestingPassword@3124587')
        user.save()

        response = APIRequestFactory().post(
            'api-token/',
            {
                'username': 'FakeTestingUsername', 
                'password': 'FakeTestingPassword@3124587',
            },
            format='json',
        )

        raw_view = obtain_auth_token(response)

        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        return
    
    def test_obtain_token_invalid_username(self):
        user = User(
            email= self.email_auth.email,
            username= 'FakeTestingUsername',
        )
        user.set_password('FakeTestingPassword@3124587')
        user.save()

        response = APIRequestFactory().post(
            'api-token/',
            {
                'username':'ThisUserDoesNotExist', 
                'password':'FakeTestingPassword@3124587',
            },
            format='json',
        )
        raw_view = obtain_auth_token(response)
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_obtain_token_invalid_password(self):
        user = User(
            email= self.email_auth.email,
            username= 'FakeTestingUsername',
        )
        user.set_password('FakeTestingPassword@3124587')
        user.save()

        response = APIRequestFactory().post(
            'api-token/',
            {
                'username':'FakeTestingUsername', 
                'password':'ThisPasswordDoesNotExist',
            },
            format='json',
        )

        raw_view = obtain_auth_token(response)
        
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
        response = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'name',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_user_by_valid_full_username(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelatedUsername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
    
    def test_query_user_by_valid_prefix_username(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelated',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_valid_user_by_full_first_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completelyDifferentFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
    
    def test_query_valid_user_by_prefix_first_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completely',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return

    def test_query_valid_user_by_full_last_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSameLastName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(raw_view.data[0], self.serialized_user.data)
        return
        
    def test_query_valid_user_by_prefix_last_name(self):
        response = APIRequestFactory().get(
            'api/users/',
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
        response = APIRequestFactory().get(
            'api/users/',
            {
                'text': 'notInTheTextAtAll',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_username(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'thisUsernameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return
    
    def test_query_user_by_invalid_prefix_username(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'sername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_first_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'thisFirstNameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return
    
    def test_query_user_by_invalid_prefix_first_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'DifferentFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_full_last_name(self):
        response = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'thisLastNameDoesNotExist',
            },
            format='json',
        )
        raw_view = UserView.as_view({'get':'list'})(response)
        self.assertEquals(len(raw_view.data), 0)
        return

    def test_query_user_by_invalid_prefix_last_name(self):
        response = APIRequestFactory().get(
            'api/users/',
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
        response = APIRequestFactory().delete('api/users/')
        raw_view = UserView.as_view({'delete':'destroy'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(email=self.valid_user.email))
        return

    def test_delete_invalid_user(self):
        response = APIRequestFactory().delete('api/users/')
        raw_view = UserView.as_view({'delete':'destroy'})(response, pk=self.unused_pk)
        self.assertEquals(raw_view.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(email=self.valid_user.email))
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
        response = APIRequestFactory().patch('api/users/')
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.unused_pk)
        self.assertEquals(raw_view.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEquals(self.valid_user, User.objects.get(email=self.valid_user.email))
        return
        
    def test_patch_valid_username(self):
        response = APIRequestFactory().patch(
            'api/users/',
            {
                'username': 'newUsername',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals('newUsername', User.objects.get(email=self.valid_user.email).username)
        return
    
    def test_patch_invalid_username(self):
        response = APIRequestFactory().patch(
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
        response = APIRequestFactory().patch(
            'api/users/',
            {
                'password': 'anotherStrongPass@9703$',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(
            authenticate(username=self.valid_user.username, 
                        password='anotherStrongPass@9703$'))
        return
    
    def test_patch_invalid_password(self):
        response = APIRequestFactory().patch(
            'api/users/',
            {
                'password': '123',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNone(
            authenticate(username=self.valid_user.username, 
                        password=self.valid_user.password))
        return

    def test_patch_first_name(self):
        response = APIRequestFactory().patch(
            'api/users/',
            {
                'first_name': 'heyMyRealFirstName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals('heyMyRealFirstName', User.objects.get(email=self.valid_user.email).first_name)
        return
    
    def test_patch_last_name(self):
        response = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': 'heyMyRealLastName',
            },
            format='json',
        )
        raw_view = UserView.as_view({'patch':'partial_update'})(response, pk=self.valid_user.pk)
        self.assertEquals(raw_view.status_code, status.HTTP_200_OK)
        self.assertEquals('heyMyRealLastName', User.objects.get(email=self.valid_user.email).last_name)
        return