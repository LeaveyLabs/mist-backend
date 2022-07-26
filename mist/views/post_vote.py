from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from mist.permissions import VotePermission
from rest_framework.permissions import IsAuthenticated

from users.models import User

from ..serializers import PostVoteSerializer
from ..models import PostVote

class PostVoteView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, VotePermission)
    serializer_class = PostVoteSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()
            
    def get_object_by_query_params(self):
        voter = self.request.query_params.get("voter")
        post = self.request.query_params.get("post")
        matching_vote = get_object_or_404(
            PostVote.objects.all(), 
            voter=voter,
            post=post)
        self.check_object_permissions(self.request, matching_vote)
        return matching_vote

    def get_queryset(self):
        """
        If parameters are missing, return all votes.
        Otherwise, return with user and post.
        """
        # parameters
        voter = self.request.query_params.get("voter")
        post = self.request.query_params.get("post")
        # filters
        queryset = PostVote.objects.all()
        if voter:
            matching_users = User.objects.filter(pk=voter)
            if not matching_users: return PostVote.objects.none()
            queryset = queryset.filter(voter=matching_users[0])
        if post:
            queryset = queryset.filter(post=post)
        return queryset