from datetime import date, datetime, timedelta
from io import BytesIO
from tempfile import TemporaryFile
from PIL import Image
from django.core import mail, cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from users.models import User
from rest_framework import status
from rest_framework.test import APIRequestFactory

from users.views.register import RegisterUserEmailView
from users.views.user import MatchingPhoneNumbersView, NearbyUsersView, UserView
from users.serializers import CompleteUserSerializer, ReadOnlyUserSerializer
from users.models import Ban, PhoneNumberAuthentication, User, EmailAuthentication

from generics import create_dummy_user_and_token_given_id

# Create your tests here.
class ThrottleTest(TestCase):
    def setUp(self):
        cache.cache.clear()
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)

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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
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
                HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
            )
            fake_response = RegisterUserEmailView.as_view()(fake_request)

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

        test_image1 = Image.open('test_assets/obama1.jpeg')
        test_image_io1 = BytesIO()
        test_image1.save(test_image_io1, format='JPEG')

        test_image2 = Image.open('test_assets/obama2.jpeg')
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


class UserViewGetTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user1.username = 'unrelatedUsername'
        self.user1.first_name = 'completelyDifferentFirstName'
        self.user1.last_name = 'notTheSameLastName'
        self.user1.save()

        self.user_serializer = CompleteUserSerializer(self.user1)

    # Serialization
    def test_get_should_return_readonly_user_given_nonmatching_token(self):
        non_matching_user, _ = create_dummy_user_and_token_given_id(2)
        user_serializer = ReadOnlyUserSerializer(non_matching_user)

        request = APIRequestFactory().get(
            'api/users/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'retrieve'})(request, pk=non_matching_user.id)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, user_serializer.data)
        return
    
    def test_get_should_return_full_user_given_matching_token(self):
        request = APIRequestFactory().get(
            'api/users/',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'retrieve'})(request, pk=self.user1.id)
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_users)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_case_insensitive_word(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'words': 'NAME',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_users)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_multiple_words(self):
        request = APIRequestFactory().get(
            'api/users/?words=name&words=not',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response_users)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelatedUsername',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'unrelated',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completelyDifferentFirstName',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return
    
    def test_get_should_return_user_given_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'completely',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSameLastName',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return
        
    def test_get_should_return_user_given_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'notTheSame',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_users[0], self.user_serializer.data)
        return

    def test_get_should_return_user_given_valid_token(self):
        serialized_users = [self.user_serializer.data]

        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': self.auth_token1,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

    def test_get_should_not_return_user_given_nonexistent_full_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'thisUsernameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return
    
    def test_get_should_not_return_user_given_nonexistent_prefix_username(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'username': 'sername',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

    def test_get_should_not_return_user_given_nonexistent_full_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'thisFirstNameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return
    
    def test_get_should_not_return_user_given_nonexistent_prefix_first_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'first_name': 'DifferentFirstName',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

    def test_get_should_not_return_user_given_nonexistent_full_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'thisLastNameDoesNotExist',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

    def test_get_should_not_return_user_given_nonexistent_prefix_last_name(self):
        request = APIRequestFactory().get(
            'api/users/',
            {
                'last_name': 'astName',
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return
    
    def test_get_should_not_return_user_given_invalid_token(self):
        invalid_token = "InvalidToken"
        request = APIRequestFactory().get(
            'api/users/',
            {
                'token': invalid_token,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'get':'list'})(request)
        response_users = response.data
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_users)
        return

class UserViewDeleteTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.unused_pk = 151

    def test_delete_should_delete_valid_user(self):
        self.assertTrue(User.objects.filter(pk=self.user1.pk))

        request = APIRequestFactory().delete('api/users/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user1.pk))
        return

    def test_delete_should_not_delete_nonexistent_user(self):
        self.assertTrue(User.objects.filter(pk=self.user1.pk))

        request = APIRequestFactory().delete('api/users/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = UserView.as_view({'delete':'destroy'})(request, pk=self.unused_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.user1.pk))
        return

class UserViewPatchTest(TestCase):
    def setUp(self):
        cache.cache.clear()

        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.unused_pk = 151

        test_image1 = Image.open('test_assets/obama1.jpeg')
        test_image_io1 = BytesIO()
        test_image1.save(test_image_io1, format='JPEG')

        test_image2 = Image.open('test_assets/obama2.jpeg')
        test_image_io2 = BytesIO()
        test_image2.save(test_image_io2, format='JPEG')

        self.image_file1 = SimpleUploadedFile('test1.jpeg', test_image_io1.getvalue(), content_type='image/jpeg')
        self.image_file2 = SimpleUploadedFile('test2.jpeg', test_image_io2.getvalue(), content_type='image/jpeg')

    def test_patch_should_not_update_given_invalid_user(self):
        self.assertFalse(User.objects.filter(pk=self.unused_pk))

        request = APIRequestFactory().patch('api/users/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.unused_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(User.objects.filter(pk=self.unused_pk))
        return
        
    def test_patch_should_update_username_given_valid_username(self):
        self.assertEqual(self.user1.username, User.objects.get(pk=self.user1.pk).username)
        fake_new_username = 'FakeNewUsername'

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': fake_new_username,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(fake_new_username.lower(), patched_user.username)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_not_update_username_given_invalid_username(self):
        self.assertEqual(self.user1.username, User.objects.get(pk=self.user1.pk).username)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'username': "$%@#",
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_update_first_name_given_first_name(self):
        fake_first_name = 'heyMyRealFirstName'

        self.assertEqual(self.user1.first_name, User.objects.get(pk=self.user1.pk).first_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'first_name': fake_first_name,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(patched_user.first_name, fake_first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertNotEqual(patched_user.first_name, fake_first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return
    
    def test_patch_should_update_last_name_given_last_name(self):
        fake_last_name = 'heyMyRealLastName'

        self.assertEqual(self.user1.last_name, User.objects.get(pk=self.user1.pk).last_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': fake_last_name,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(patched_user.last_name, fake_last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_not_update_last_name_given_invalid_last_name(self):
        fake_last_name = '++**&&'

        self.assertEqual(self.user1.last_name, User.objects.get(pk=self.user1.pk).last_name)

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'last_name': fake_last_name,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertNotEqual(patched_user.last_name, fake_last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        self.assertFalse(patched_user.picture)
        return

    def test_patch_should_update_picture_given_valid_picture(self):
        pre_patched_user = User.objects.get(pk=self.user1.pk)
        self.assertFalse(pre_patched_user.picture)

        request = APIRequestFactory().patch(
            'api/users/', 
            encode_multipart(boundary=BOUNDARY, data={
                'picture': self.image_file1,
                'confirm_picture': self.image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(patched_user.picture)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        return
    
    def test_patch_should_not_update_picture_given_invalid_picture(self):
        ten_mb_limit = (1024 * 1024 * 10)
        pre_patched_user = User.objects.get(pk=self.user1.pk)
        self.assertFalse(pre_patched_user.picture)

        with TemporaryFile() as temp_file:
            temp_file.seek(ten_mb_limit)
            temp_file.write(b'0')

            request = APIRequestFactory().patch(
                'api/users/', 
                encode_multipart(boundary=BOUNDARY, data={'picture': temp_file}),
                content_type=MULTIPART_CONTENT,
                HTTP_AUTHORIZATION=f"Token {self.auth_token1}"
            )
            response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
            patched_user = User.objects.get(pk=self.user1.pk)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(patched_user.picture)
            self.assertEqual(self.user1.email, patched_user.email)
            self.assertEqual(self.user1.username, patched_user.username)
            self.assertEqual(self.user1.first_name, patched_user.first_name)
            self.assertEqual(self.user1.last_name, patched_user.last_name)
            self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
        return

    def test_patch_should_update_latitude_given_valid_latitude(self):
        new_latitude = 1.0

        request = APIRequestFactory().patch(
            'api/users/',
            {
                'latitude': new_latitude,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user1.email, patched_user.email)
        self.assertEqual(self.user1.username, patched_user.username)
        self.assertEqual(self.user1.first_name, patched_user.first_name)
        self.assertEqual(self.user1.last_name, patched_user.last_name)
        self.assertEqual(self.user1.date_of_birth, patched_user.date_of_birth)
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
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = UserView.as_view({'patch':'partial_update'})(request, pk=self.user1.pk)
        patched_user = User.objects.get(pk=self.user1.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(patched_user.keywords, lowercased_new_keywords)
        return

class MatchingPhoneNumbersViewTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)
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
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)
        return

    def test_get_should_not_return_given_no_auth_user(self):
        request = APIRequestFactory().get(
            'api/nearby-users/',
        )
        response = NearbyUsersView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return

    def test_get_should_return_only_nearby_users(self):
        self.user1.latitude = 0
        self.user1.longitude = 0
        self.user1.save()

        self.user2.latitude = 0
        self.user2.longitude = 0
        self.user2.save()

        self.user3.latitude = 100
        self.user3.longitude = 100
        self.user3.save()

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