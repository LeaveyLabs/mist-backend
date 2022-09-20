from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Block, Post
from mist.serializers import BlockSerializer
from mist.views.block import BlockView

from users.tests.generics import create_dummy_user_and_token_given_id

@freeze_time("2020-01-01")
class BlockTest(TestCase):
    def setUp(self):
        self.user1, self.auth_token1 = create_dummy_user_and_token_given_id(1)
        self.user2, self.auth_token2 = create_dummy_user_and_token_given_id(2)

        self.post = Post.objects.create(
            title='FakeTitleForFirstPost',
            body='FakeTextForFirstPost',
            author=self.user1,
        )

        self.unused_pk = 151
        return
    
    def test_get_should_return_block_given_valid_blocked_user(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocked_user': block.blocked_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_block = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_block, serialized_block)
        return
    
    def test_get_should_not_return_block_given_invalid_blocked_user(self):
        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocked_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_blocks = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_blocks)
        return
    
    def test_get_should_return_block_given_valid_blocking_user(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocking_user': block.blocking_user.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_block = response.data[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_block, serialized_block)
        return
    
    def test_get_should_not_return_block_given_invalid_blocking_user(self):
        request = APIRequestFactory().get(
            '/api/blocks',
            {
                'blocking_user': self.user1.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'get':'list'})(request)
        response_blocks = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response_blocks)
        return

    def test_post_should_create_block_given_valid_block(self):
        block = Block(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,
        )
        serialized_block = BlockSerializer(block).data

        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
            blocked_user=self.user2,
        ))

        request = APIRequestFactory().post(
            '/api/blocks',
            serialized_block,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'post':'create'})(request)
        response_block = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_block.get('blocking_user'), serialized_block.get('blocking_user'))
        self.assertEqual(response_block.get('blocked_user'), serialized_block.get('blocked_user'))
        self.assertTrue(Block.objects.filter(
            blocking_user=self.user1,
            blocked_user=self.user2,
        ))
        return
    
    def test_post_should_not_create_block_given_invalid_block(self):
        block = Block(
            blocking_user=self.user1,
        )
        serialized_block = BlockSerializer(block).data

        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
        ))

        request = APIRequestFactory().post(
            '/api/blocks',
            serialized_block,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = BlockView.as_view({'post':'create'})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Block.objects.filter(
            blocking_user=self.user1,
        ))
        return
    
    def test_delete_should_delete_block_given_pk(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))

        request = APIRequestFactory().delete('/api/delete-block/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request, pk=block.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Block.objects.filter(pk=block.pk))
        return
    
    def test_delete_should_delete_block_given_blocking_and_blocked_user(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))

        request = APIRequestFactory().delete(
            f'/api/delete-block/?blocking_user={self.user1.pk}&blocked_user={self.user2.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Block.objects.filter(pk=block.pk))
        return
    
    def test_delete_should_not_delete_block_given_no_parameters(self):
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))

        request = APIRequestFactory().delete(
            f'/api/delete-block/', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Block.objects.filter(pk=block.pk))
        return

    def test_delete_should_not_delete_block_given_nonexistent_pk(self):
        nonexistent_pk = -1
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))
        self.assertFalse(Block.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete(
            f'/api/delete-block/', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Block.objects.filter(pk=block.pk))
        return
    
    def test_delete_should_not_delete_block_given_invalid_query_combo(self):
        nonexistent_pk = -1
        block = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block.pk))
        self.assertFalse(Block.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete(
            f'/api/delete-block/?blocking_user={self.user1.pk}&blocked_user={self.user1.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Block.objects.filter(pk=block.pk))
        return
    
    def test_delete_should_delete_block_given_pk_and_query_combo(self):
        block_1 = Block.objects.create(
            blocking_user=self.user1,
            blocked_user=self.user2,
            timestamp=0,        
        )
        block_2 = Block.objects.create(
            blocking_user=self.user2,
            blocked_user=self.user1,
            timestamp=0,        
        )

        self.assertTrue(Block.objects.filter(pk=block_1.pk))
        self.assertTrue(Block.objects.filter(pk=block_2.pk))

        request = APIRequestFactory().delete(
            f'/api/delete-block/?blocking_user={self.user1.pk}&blocked_user={self.user2.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}')
        response = BlockView.as_view({'delete':'destroy'})(request, pk=block_1.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Block.objects.filter(pk=block_1.pk))
        self.assertTrue(Block.objects.filter(pk=block_2.pk))
        return