from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Favorite, Post
from mist.serializers import FavoriteSerializer
from mist.views.favorite import FavoriteView

from users.models import User

@freeze_time("2020-01-01")
class FavoriteTest(TestCase):
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
        return

    def test_get_should_return_favorites_given_favoriting_user(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        request = APIRequestFactory().get(
            '/api/favorites/',
            {
              'favoriting_user': self.user1.pk,  
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'get':'list'})(request)
        response_favorite = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_favorite, serialized_favorite)
        return

    def test_get_should_not_return_favorites_given_nonexistent_favoriting_user(self):
        request = APIRequestFactory().get(
            '/api/favorites/',
            {
              'favoriting_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'get':'list'})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data)
        return
    
    def test_post_should_create_favorite_given_valid_favorite(self):
        favorite = Favorite(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        self.assertFalse(Favorite.objects.filter(
            timestamp=favorite.timestamp,
            post=favorite.post,
            favoriting_user=favorite.favoriting_user,
        ))

        request = APIRequestFactory().post(
            '/api/favorites/',
            serialized_favorite,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'post':'create'})(request)
        response_favorite = response.data
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_favorite.get('post'),
                        serialized_favorite.get('post'))
        self.assertEqual(response_favorite.get('favoriting_user'),
                        serialized_favorite.get('favoriting_user'))
        self.assertTrue(Favorite.objects.filter(
            timestamp=favorite.timestamp,
            post=favorite.post,
            favoriting_user=favorite.favoriting_user,
        ))
        return
    
    def test_post_should_not_create_favorite_given_invalid_favorite(self):
        favorite = Favorite(
            timestamp=0,
            favoriting_user=self.user1
        )
        serialized_favorite = FavoriteSerializer(favorite).data

        request = APIRequestFactory().post(
            '/api/favorites/',
            serialized_favorite,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = FavoriteView.as_view({'post':'create'})(request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        return
    
    def test_delete_should_delete_favorite_given_pk(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )
        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))

        request = APIRequestFactory().delete('/api/favorite/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request, pk=favorite.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(pk=favorite.pk))
        return

    def test_delete_should_delete_favorite_given_query_combo(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )

        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))

        request = APIRequestFactory().delete(
            f'/api/favorite/?favoriting_user={favorite.favoriting_user.pk}&post={favorite.post.pk}',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(pk=favorite.pk))
        return
    
    def test_delete_should_not_delete_favorite_given_no_parameters(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )

        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))

        request = APIRequestFactory().delete('/api/favorite/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))
        return

    def test_delete_should_not_delete_favorite_given_nonexistent_pk(self):
        nonexistent_pk = -1
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )

        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))
        self.assertFalse(Favorite.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete('/api/favorite/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))
        return
    
    def test_delete_should_not_delete_favorite_given_invalid_query_combo(self):
        favorite = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )

        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))

        request = APIRequestFactory().delete(
            f'/api/favorite/?favoriting_user={self.user2.pk}&post={favorite.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token2}')
        response = FavoriteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(pk=favorite.pk))
        return
    
    def test_delete_should_delete_favorite_with_pk_given_pk_and_query_combo(self):
        favorite_1 = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user1,
        )
        favorite_2 = Favorite.objects.create(
            timestamp=0,
            post=self.post,
            favoriting_user=self.user2,
        )

        self.assertTrue(Favorite.objects.filter(pk=favorite_1.pk))
        self.assertTrue(Favorite.objects.filter(pk=favorite_2.pk))

        request = APIRequestFactory().delete(
            f'/api/favorite/?favoriting_user={favorite_1.favoriting_user.pk}&post={favorite_1.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = FavoriteView.as_view({'delete':'destroy'})(request, pk=favorite_1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.filter(pk=favorite_1.pk))
        self.assertTrue(Favorite.objects.filter(pk=favorite_2.pk))
        return