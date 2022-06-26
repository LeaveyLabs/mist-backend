from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Post, Tag
from mist.serializers import TagSerializer
from mist.views.tag import TagView

from users.models import User

class TagTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser1@usc.edu',
            username='TestUser1',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword1@98374")
        self.user1.save()
        self.auth_token1 = Token.objects.create(user=self.user1)

        self.user2 = User(
            email='TestUser2@usc.edu',
            username='TestUser2',
            date_of_birth=date(2000, 1, 1),
        )
        self.user2.set_password("TestPassword2@98374")
        self.user2.save()
        self.auth_token2 = Token.objects.create(user=self.user2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )

        self.unused_pk = 151
        return
    
    def test_get_should_return_tag_given_valid_tagged_user(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user1,
            tagging_user=self.user2,
            timestamp=0,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagged_user': tag.tagged_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tag, serialized_tag)
        return
    
    def test_get_should_not_return_tag_given_invalid_tagged_user(self):
        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagged_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_tags)
        return
    
    def test_get_should_return_tag_given_valid_tagging_user(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user1,
            tagging_user=self.user2,
            timestamp=0,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagging_user': tag.tagging_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tag = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_tag, serialized_tag)
        return

    def test_get_should_not_return_tag_given_invalid_tagging_user(self):
        request = APIRequestFactory().get(
            '/api/tags',
            {
                'tagging_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'get':'list'})(request)
        response_tags = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_tags)
        return

    def test_post_should_create_tag_given_valid_tag(self):
        tag = Tag(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)
        response_tag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_tag.get('post'), serialized_tag.get('post'))
        self.assertEqual(response_tag.get('tagged_user'), serialized_tag.get('tagged_user'))
        self.assertEqual(response_tag.get('tagging_user'), serialized_tag.get('tagging_user'))
        self.assertTrue(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
            tagged_user=self.user2,
        ))
        return
    
    def test_post_should_not_create_tag_given_invalid_tag(self):
        tag = Tag(
            post=self.post,
            tagging_user=self.user1,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
        ))

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Tag.objects.filter(
            post=self.post,
            tagging_user=self.user1,
        ))
        return
    
    def test_delete_should_delete_tag(self):
        tag = Tag.objects.create(
            post=self.post,
            tagged_user=self.user2,
            tagging_user=self.user1,            
        )

        self.assertTrue(Tag.objects.filter(pk=tag.pk))

        request = APIRequestFactory().delete('/api/tags/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = TagView.as_view({'delete':'destroy'})(request, pk=tag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=tag.pk))
        return