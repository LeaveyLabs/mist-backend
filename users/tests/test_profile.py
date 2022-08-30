from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY
from rest_framework import status
from rest_framework.test import APIRequestFactory
from users.models import User

from users.tests.generics import create_dummy_user_and_token_given_id, create_simple_uploaded_file_from_image_path
from users.views.profile import VerifyProfilePicture


class VerifyProfilePictureTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user1.picture = None
        self.user1.save()

        self.obama_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/obama1.jpeg', 
            'obama1.jpeg')
        self.obama_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/obama2.jpeg', 
            'obama2.jpeg')
        self.kevin_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/kevin1.jpeg', 
            'kevin1.jpeg')
        self.kevin_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/kevin2.jpeg', 
            'kevin2.jpeg')
        self.adam_image_file1 = create_simple_uploaded_file_from_image_path(
            'test_assets/adam1.jpeg', 
            'adam1.jpeg')
        self.adam_image_file2 = create_simple_uploaded_file_from_image_path(
            'test_assets/adam2.jpeg', 
            'adam2.jpeg')

    def test_post_should_return_success_given_two_obamas(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.obama_image_file1,
                'confirm_picture': self.obama_image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(patched_user.picture)
        return

    def test_post_should_return_success_given_two_kevins(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.kevin_image_file1,
                'confirm_picture': self.kevin_image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(patched_user.picture)
        return
    
    def test_post_should_return_success_given_two_adams(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.adam_image_file1,
                'confirm_picture': self.adam_image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(patched_user.picture)
        return
    
    def test_post_should_return_failure_given_obama_and_kevin(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.obama_image_file1,
                'confirm_picture': self.kevin_image_file2,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(patched_user.picture)
        return
    
    def test_post_should_return_failure_given_obama_and_adam(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.obama_image_file1,
                'confirm_picture': self.adam_image_file1,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(patched_user.picture)
        return
    
    def test_post_should_return_failure_given_adam_and_kevin(self):
        request = APIRequestFactory().post(
            'api-verify-profile-picture',
            encode_multipart(boundary=BOUNDARY, data=
            {
                'picture': self.adam_image_file1,
                'confirm_picture': self.kevin_image_file1,
            }),
            content_type=MULTIPART_CONTENT,
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VerifyProfilePicture.as_view()(request)
        patched_user = User.objects.get(id=self.user1.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(patched_user.picture)
        return