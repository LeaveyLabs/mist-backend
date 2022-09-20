from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Post
from mist.views.word import WordView

from users.models import User
from users.tests.generics import create_dummy_user_and_token_given_id

@freeze_time("2020-01-01")
class WordTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)
        self.user3, self.auth_token3 = create_dummy_user_and_token_given_id(3)

    def test_get_should_return_matching_words_given_partial_word(self):
        word_to_search = 'Fake'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user1,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 1)
        return
    
    def test_get_should_return_matching_words_given_full_word(self):
        word_to_search = 'FakeTitleForFakePost'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user1,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 1)
        return
    
    def test_get_should_not_return_words_with_zero_occurrences(self):
        word_to_search = 'thisWordDoesNotExist'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user1,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_get_should_return_non_zero_occurrences_given_partial_search_word_and_multiple_wrapper_words_in_post(self):
        word_to_search = 'Fake'
        wrapper_word1 = 'Title'
        wrapper_word2 = 'Post'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user1,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}&wrapper_words={wrapper_word1}&wrapper_words={wrapper_word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 1)
        return

    def test_get_should_return_zero_occurrences_given_search_word_and_multiple_wrapper_words_not_in_post(self):
        word_to_search = 'Fake'
        wrapper_word1 = 'ThisWordDoesNotExist'
        wrapper_word2 = 'ThisWordDoesNotExistEither'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user1,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}&wrapper_words={wrapper_word1}&wrapper_words={wrapper_word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 0)
        return