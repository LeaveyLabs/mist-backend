from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, Post, Tag
from mist.serializers import TagSerializer
from mist.views.tag import TagView

import sys
sys.path.append("...")
from twilio_config import TwillioTestClientMessages

from users.models import User

@freeze_time("2020-01-01")
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

        self.comment = Comment.objects.create(
            body='FakeTextForFirstPost',
            author=self.user1,
            post=self.post,
        )

        self.unused_pk = 151
        return
    
    def test_get_should_return_tag_given_valid_tagged_user(self):
        tag = Tag.objects.create(
            comment=self.comment,
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
    
    def test_get_should_return_tag_given_comment(self):
        tag = Tag.objects.create(
            comment=self.comment,
            tagged_user=self.user1,
            tagging_user=self.user2,
            timestamp=0,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().get(
            '/api/tags',
            {
                'comment': self.comment.id,
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
            comment=self.comment,
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

    def test_post_should_create_tag_given_valid_tag_with_tagging_user(self):
        tag = Tag(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            comment=self.comment,
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
        self.assertEqual(response_tag.get('comment'), serialized_tag.get('comment'))
        self.assertEqual(response_tag.get('tagged_user'), serialized_tag.get('tagged_user'))
        self.assertEqual(response_tag.get('tagging_user'), serialized_tag.get('tagging_user'))
        self.assertTrue(Tag.objects.filter(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
        ))
        return
    
    def test_post_should_create_tag_given_valid_tag_with_phone_number(self):
        test_phone_number = "+12134789920"

        tag = Tag(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)
        response_tag = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_tag.get('comment'), serialized_tag.get('comment'))
        self.assertEqual(response_tag.get('tagging_user'), serialized_tag.get('tagging_user'))
        self.assertEqual(response_tag.get('tagged_name'), serialized_tag.get('tagged_name'))
        self.assertEqual(response_tag.get('tagged_phone_number'), serialized_tag.get('tagged_phone_number'))
        self.assertTrue(Tag.objects.filter(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
        ))
        return

    def test_post_should_send_text_given_valid_tag_with_phone_number(self):
        test_phone_number = "+12134789920"

        tag = Tag(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)

        messages = TwillioTestClientMessages.created
        matching_messages = []
        for message in messages:
            if message.get('to') == test_phone_number:
                matching_messages.append(message)
        

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(matching_messages)
        return
    
    def test_post_should_not_create_tag_given_neither_tagged_user_or_phone_number(self):
        tag = Tag(
            comment=self.comment,
            tagging_user=self.user1,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            comment=self.comment,
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
            comment=self.comment,
            tagging_user=self.user1,
        ))
        return
    
    def test_post_should_not_create_tag_given_with_both_tagged_user_and_phone_number(self):
        test_phone_number = "+12134789920"

        tag = Tag(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
        )
        serialized_tag = TagSerializer(tag).data

        self.assertFalse(Tag.objects.filter(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
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
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
            tagged_name=self.user2.username,
            tagged_phone_number=test_phone_number,
        ))
        return

    def test_post_should_not_create_tag_given_with_nonunique_tagging_taggged_user(self):
        tag = Tag.objects.create(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_user=self.user2,
            tagged_name=self.user2.username,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_post_should_not_create_tag_given_with_nonunique_tagging_tagged_phone_number(self):
        test_phone_number = "+12134789920"
        
        tag = Tag.objects.create(
            comment=self.comment,
            tagging_user=self.user1,
            tagged_phone_number=test_phone_number,
            tagged_name=self.user2.username,
        )
        serialized_tag = TagSerializer(tag).data

        request = APIRequestFactory().post(
            '/api/tags',
            serialized_tag,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = TagView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return

    def test_delete_should_delete_tag(self):
        tag = Tag.objects.create(
            comment=self.comment,
            tagged_user=self.user2,
            tagging_user=self.user1,            
        )

        self.assertTrue(Tag.objects.filter(pk=tag.pk))

        request = APIRequestFactory().delete('/api/tags/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = TagView.as_view({'delete':'destroy'})(request, pk=tag.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=tag.pk))
        return