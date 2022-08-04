from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Post, PostVote
from mist.serializers import PostVoteSerializer
from mist.views.post_vote import PostVoteView

from users.models import User

@freeze_time("2020-01-01")
class PostVoteTest(TestCase):
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
    
    def test_post_should_create_vote_given_valid_vote_without_emoji(self):
        vote = PostVote(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        serialized_vote = PostVoteSerializer(vote).data

        self.assertFalse(PostVote.objects.filter(
            voter=vote.voter,
            post=vote.post,
        ))

        request = APIRequestFactory().post(
            '/api/votes',
            serialized_vote,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostVoteView.as_view({'post':'create'})(request)

        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_vote.get('voter'), serialized_vote.get('voter'))
        self.assertEqual(response_vote.get('post'), serialized_vote.get('post'))
        self.assertEqual(response_vote.get('rating'), serialized_vote.get('rating'))
        self.assertTrue(PostVote.objects.filter(
            voter=vote.voter,
            post=vote.post,
        ))
        return
    
    def test_post_should_create_vote_given_valid_vote_with_emoji(self):
        vote = PostVote(
            voter=self.user1,
            post=self.post,
            rating=10,
            emoji="😭",
        )
        serialized_vote = PostVoteSerializer(vote).data

        self.assertFalse(PostVote.objects.filter(
            voter=vote.voter,
            post=vote.post,
        ))

        request = APIRequestFactory().post(
            '/api/votes',
            serialized_vote,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostVoteView.as_view({'post':'create'})(request)

        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_vote.get('voter'), serialized_vote.get('voter'))
        self.assertEqual(response_vote.get('post'), serialized_vote.get('post'))
        self.assertEqual(response_vote.get('rating'), serialized_vote.get('rating'))
        self.assertEqual(response_vote.get('emoji'), serialized_vote.get('emoji'))
        self.assertTrue(PostVote.objects.filter(
            voter=vote.voter,
            post=vote.post,
            emoji=vote.emoji,
        ))
        return
    
    def test_delete_should_delete_vote_given_pk(self):
        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostVote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_delete_vote_given_voter_and_post(self):
        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={vote.voter.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostVote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_not_delete_vote_given_no_parameters(self):
        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_not_delete_vote_given_nonexistent_pk(self):
        nonexistent_pk = 99999
        self.assertFalse(PostVote.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete('/api/votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(PostVote.objects.filter(pk=nonexistent_pk))
        return

    def test_delete_should_not_delete_vote_given_invalid_voter_post_combination(self):
        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))
        self.assertFalse(PostVote.objects.filter(
            voter=self.user2.pk, 
            post=vote.post.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={self.user2.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_delete_vote_given_pk_and_query_combo(self):
        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )
        self.assertTrue(PostVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/votes?voter={vote.voter.pk}&post={vote.post.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = PostVoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PostVote.objects.filter(pk=vote.pk))
        return
    
    def test_get_should_return_votes_by_voter_on_post_given_voter_and_post(self):
        vote1 = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            timestamp=0,
            rating=10,
            emoji="😭",
        )
        vote2 = PostVote.objects.create(
            voter=self.user2,
            post=self.post,
            timestamp=0,
            rating=10,
        )
        serialized_vote = PostVoteSerializer(vote1).data
        self.assertTrue(PostVote.objects.filter(
            voter=vote1.voter,
            post=vote1.post,
            timestamp=vote1.timestamp,
            rating=vote1.rating,
        ))
        self.assertTrue(PostVote.objects.filter(
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
        response = PostVoteView.as_view({'get':'list'})(request)
        response_vote = response.data[0]

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_vote, response_vote)
        return
    
    def test_patch_should_update_emoji_given_emoji(self):
        new_emoji = "🤠"

        vote = PostVote.objects.create(
            voter=self.user1,
            post=self.post,
            rating=10,
        )

        request = APIRequestFactory().patch(
            f'/api/votes/?voter={vote.voter.pk}&post={vote.post.pk}',
            {
                'emoji': new_emoji,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = PostVoteView.as_view({'patch':'partial_update'})(request)
        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_vote.get('emoji'), new_emoji)
        self.assertTrue(PostVote.objects.filter(
            voter=vote.voter, 
            post=vote.post,
            emoji=new_emoji))