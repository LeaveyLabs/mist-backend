from django.db.models import Count
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .serializers import (
    ProfileSerializer, 
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    UserSerializer,
)
from .models import (
    Profile, 
    Post, 
    Comment,
    Message,
)

# Create your views here.
class ProfileView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_queryset(self):
        """
        Returns profiles matching the username.
        """
        username = self.request.query_params.get('username')
        return Profile.objects.filter(username=username)

class PostView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer
    # will return all objects in order of votes
    queryset = Post.objects.annotate(vote_count=Count('votes')).order_by('-vote_count')

class CommentView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """
        Returns comments matching the post_id.
        """
        post_id = self.request.query_params.get('post_id')
        return Comment.objects.filter(post_id=post_id)

class MessageView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

class UserCreate(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = UserSerializer
    queryset = User.objects.all()