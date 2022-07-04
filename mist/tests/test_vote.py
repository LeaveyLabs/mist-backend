from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Post, Vote
from mist.serializers import VoteSerializer
from mist.views.vote import VoteView

from users.models import User

class VoteTest(TestCase):
    def setUp(self):
        self.user1 = User(
            email='TestUser@usc.edu',
            username='TestUser',
            date_of_birth=date(2000, 1, 1),
        )
        self.user1.set_password("TestPassword@98374")
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
    
    def test_post_should_create_vote_given_valid_vote(self):
        vote = Vote(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote).data

        self.assertFalse(Vote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            rating=vote.rating,
        ))

        request = APIRequestFactory().post(
            '/api/votes',
            serialized_vote,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VoteView.as_view({'post':'create'})(request)

        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_vote.get('voter'), serialized_vote.get('voter'))
        self.assertEqual(response_vote.get('post'), serialized_vote.get('post'))
        self.assertEqual(response_vote.get('rating'), serialized_vote.get('rating'))
        self.assertTrue(Vote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            rating=vote.rating,
        ))
        return
    
    def test_delete_should_delete_vote_given_pk(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_delete_vote_given_voter_and_post(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={vote.voter.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_not_delete_vote_given_no_parameters(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Vote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_not_delete_vote_given_nonexistent_pk(self):
        nonexistent_pk = 99999
        self.assertFalse(Vote.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Vote.objects.filter(pk=nonexistent_pk))
        return

    def test_delete_should_not_delete_vote_given_invalid_voter_post_combination(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))
        self.assertFalse(Vote.objects.filter(
            voter=self.user2.pk, 
            post=vote.post.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={self.user2.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Vote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_delete_vote_given_pk_and_query_combo(self):
        vote = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(Vote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={vote.voter.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = VoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vote.objects.filter(pk=vote.pk))
        return
    
    def test_get_should_return_votes_by_voter_on_post_given_voter_and_post(self):
        vote1 = Vote.objects.create(
            voter=self.user1,
            post=self.post,
            timestamp=0,
            rating=10,
        )
        vote2 = Vote.objects.create(
            voter=self.user2,
            post=self.post,
            timestamp=0,
            rating=10,
        )
        serialized_vote = VoteSerializer(vote1).data
        self.assertTrue(Vote.objects.filter(
            voter=vote1.voter,
            post=vote1.post,
            timestamp=vote1.timestamp,
            rating=vote1.rating,
        ))
        self.assertTrue(Vote.objects.filter(
            voter=vote2.voter,
            post=vote2.post,
            timestamp=vote2.timestamp,
            rating=vote2.rating,
        ))

        request = APIRequestFactory().get(
            '/api/votes/',
            {
                'voter': vote1.voter.pk,
                'post': vote1.post.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = VoteView.as_view({'get':'list'})(request)
        response_vote = response.data[0]

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_vote, response_vote)
        return