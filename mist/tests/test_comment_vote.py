from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from mist.models import Comment, Post, CommentVote
from mist.serializers import CommentVoteSerializer
from mist.views.comment_vote import CommentVoteView

from users.models import User

@freeze_time("2020-01-01")
class CommentVoteTest(TestCase):
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
        self.comment = Comment.objects.create(
            body='FakeTextForFirstPost',
            author=self.user1,
            post=self.post,
        )
        return
    
    def test_post_should_create_vote_given_valid_vote(self):
        vote = CommentVote(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        serialized_vote = CommentVoteSerializer(vote).data

        self.assertFalse(CommentVote.objects.filter(
            voter=vote.voter,
            comment=vote.comment,
            rating=vote.rating,
        ))

        request = APIRequestFactory().post(
            '/api/comment-votes',
            serialized_vote,
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentVoteView.as_view({'post':'create'})(request)

        response_vote = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_vote.get('voter'), serialized_vote.get('voter'))
        self.assertEqual(response_vote.get('comment'), serialized_vote.get('comment'))
        self.assertEqual(response_vote.get('rating'), serialized_vote.get('rating'))
        self.assertTrue(CommentVote.objects.filter(
            voter=vote.voter,
            comment=vote.comment,
            rating=vote.rating,
        ))
        return
    
    def test_delete_should_delete_vote_given_pk(self):
        vote = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/comment-votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_delete_vote_given_voter_and_comment(self):
        vote = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/comment-votes?voter={vote.voter.pk}&comment={vote.comment.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_not_delete_vote_given_no_parameters(self):
        vote = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete('/api/comment-votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))
        return

    def test_delete_should_not_delete_vote_given_nonexistent_pk(self):
        nonexistent_pk = 99999
        self.assertFalse(CommentVote.objects.filter(pk=nonexistent_pk))

        request = APIRequestFactory().delete('/api/comment-votes/', HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request, pk=nonexistent_pk)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(CommentVote.objects.filter(pk=nonexistent_pk))
        return

    def test_delete_should_not_delete_vote_given_invalid_voter_comment_combination(self):
        vote = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))
        self.assertFalse(CommentVote.objects.filter(
            voter=self.user2.pk, 
            comment=vote.comment.pk))

        request = APIRequestFactory().delete(
            f'/api/comment-votes?voter={self.user2.pk}&comment={vote.comment.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request, pk='')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))
        return
    
    def test_delete_should_delete_vote_given_pk_and_query_combo(self):
        vote = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            rating=10,
        )
        self.assertTrue(CommentVote.objects.filter(pk=vote.pk))

        request = APIRequestFactory().delete(
            f'/api/comment-votes?voter={vote.voter.pk}&comment={vote.comment.pk}', 
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',)
        response = CommentVoteView.as_view({'delete':'destroy'})(request, pk=vote.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CommentVote.objects.filter(pk=vote.pk))
        return
    
    def test_get_should_return_votes_by_voter_on_comment_given_voter_and_comment(self):
        vote1 = CommentVote.objects.create(
            voter=self.user1,
            comment=self.comment,
            timestamp=0,
            rating=10,
        )
        vote2 = CommentVote.objects.create(
            voter=self.user2,
            comment=self.comment,
            timestamp=0,
            rating=10,
        )
        serialized_vote = CommentVoteSerializer(vote1).data
        self.assertTrue(CommentVote.objects.filter(
            voter=vote1.voter,
            comment=vote1.comment,
            timestamp=vote1.timestamp,
            rating=vote1.rating,
        ))
        self.assertTrue(CommentVote.objects.filter(
            voter=vote2.voter,
            comment=vote2.comment,
            timestamp=vote2.timestamp,
            rating=vote2.rating,
        ))

        request = APIRequestFactory().get(
            '/api/comment-votes/',
            {
                'voter': vote1.voter.pk,
                'comment': vote1.comment.pk,
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.auth_token1}',
        )
        response = CommentVoteView.as_view({'get':'list'})(request)
        response_vote = response.data[0]

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serialized_vote, response_vote)
        return