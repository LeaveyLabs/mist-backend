import re
from django.db.models import Avg
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.postgres.search import SearchVector

from .serializers import (
    FlagSerializer,
    ProfileSerializer, 
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    RegisterRequestSerializer,
    ValidationRequestSerializer,
    VoteSerializer,
)
from .models import (
    Profile, 
    Post, 
    Comment,
    Message,
    Vote,
)

# Create your views here.
class ProfileView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_queryset(self):
        """
        Returns profiles matching the username.
        """
        # parameters
        username = self.request.query_params.get('username')
        text = self.request.query_params.get('text')
        # filter
        if username == None and text == None:
            return []
        elif username != None:
            return Profile.objects.filter(username=username)
        else:
            return Profile.objects.annotate(
                search=SearchVector('username', 
                'first_name', 'last_name')
                ).filter(search__contains=text)

class PostView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        """
        Filter by text, location, and date. 
        If a parameter does not exist, then skip it. 
        Sort the result by vote ratings. 
        """
        # parameters
        text = self.request.query_params.get('text')
        location = self.request.query_params.get('location')
        timestamp = self.request.query_params.get('timestamp')
        # filter
        queryset = Post.objects.all()
        if text != None: 
            queryset = Post.objects.annotate(
                search=SearchVector('text', 'title')
            ).filter(search__contains=text)
        if location != None:
            queryset = queryset.filter(location=location)
        if timestamp != None:
            queryset = queryset.filter(timestamp=timestamp)
        # order
        return queryset.annotate(
            vote_count=Avg('vote__rating', default=0)
            ).order_by('-vote_count')

class CommentView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """
        Returns comments matching the post_id.
        """
        post_id = self.request.query_params.get('post_id')
        return Comment.objects.filter(post_id=post_id)

class VoteView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = VoteSerializer

    def get_queryset(self):
        """
        If parameters are missing, return all votes. 
        Otherwise, return with username and post_id.
        """
        # parameters
        username = self.request.query_params.get("username")
        post_id = self.request.query_params.get("post_id")
        # filters
        if username == None or post_id == None:
            return Vote.objects.all()
        else:
            return Vote.objects.filter(voter=username, post_id=post_id)

class FlagView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = FlagSerializer
    queryset = Vote.objects.all()

class MessageView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

class ValidateView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = ValidationRequestSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = RegisterRequestSerializer