from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Post
from mist.views.word import WordView

from users.models import User

class WordTest(TestCase):
    def setUp(self):
        self.user = User(
            email='TestUser@usc.edu',
            username='TestUser',
            date_of_birth=date(2000, 1, 1),
        )
        self.user.set_password("TestPassword@98374")
        self.user.save()
        self.auth_token = Token.objects.create(user=self.user)

    def test_get_should_return_matching_words_given_partial_word(self):
        word_to_search = 'Fake'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            author=self.user,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 1)
        return
    
    def test_get_should_return_non_zero_occurrences_given_partial_search_word_and_multiple_wrapper_words_in_post(self):
        word_to_search = 'Fake'
        wrapper_word1 = 'Title'
        wrapper_word2 = 'Post'
        Post.objects.create(
            title='FakeTitleForFakePost',
            body='FakeTextForFakePost',
            author=self.user,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}&wrapper_words={wrapper_word1}&wrapper_words={wrapper_word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
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
            author=self.user,
        )

        request = APIRequestFactory().get(
            f'/api/words?search_word={word_to_search}&wrapper_words={wrapper_word1}&wrapper_words={wrapper_word2}',
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token}',
        )
        response = WordView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for word in response.data:
            self.assertTrue(word_to_search.lower() in word.get('text'))
            self.assertEqual(word.get('occurrences'), 0)
        return