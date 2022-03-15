from datetime import datetime
from django.db.models import Avg
from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User

from .serializers import (
    FlagSerializer,
    ProfileSerializer, 
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    RegistrationSerializer,
    UserCreateRequestSerializer,
    ValidationSerializer,
    VoteSerializer,
    WordSerializer,
)
from .models import (
    Profile, 
    Post, 
    Comment,
    Message,
    Registration,
    Vote,
    Word,
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
            username_set = Profile.objects.filter(username__contains=text)
            first_name_set = Profile.objects.filter(first_name__contains=text)
            last_name_set = Profile.objects.filter(last_name__contains=text)
            return (username_set | first_name_set | last_name_set).distinct()

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
            text_set = Post.objects.filter(text__contains=text)
            title_set = Post.objects.filter(title__contains=text)
            queryset = (text_set | title_set).distinct()
        if location != None:
            queryset = queryset.filter(location=location)
        if timestamp != None:
            queryset = queryset.filter(timestamp=timestamp)
        # order
        return queryset.annotate(
            vote_count=Avg('vote__rating', default=0)
            ).order_by('-vote_count')

class WordView(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = WordSerializer

    def get_queryset(self):
        # parameters
        text = self.request.query_params.get('text')
        # filter
        if text == None: return []
        return Word.objects.filter(text__contains=text)

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

class RegisterView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = RegistrationSerializer

class ValidateView(generics.CreateAPIView):
    """
    View to validate users. 
    """
    permission_classes = (AllowAny, )
    serializer_class = ValidationSerializer

    def post(self, request, format=None):
        # check validation request
        validation = ValidationSerializer(data=request.data)
        # if the data is not valid
        if not validation.is_valid():
            # return error
            return Response(
                {"status": "error", 
                "data": validation.errors}, 
                status=status.HTTP_400_BAD_REQUEST)
        # if the data is valid
        else:
            # mark registration as validated
            registration = Registration.objects.get(email=validation.data['email'])
            registration.validated = True
            registration.validation_time = datetime.now().timestamp()
            registration.save()
            return Response(
                {"status": "success"}, 
                status=status.HTTP_200_OK)

class CreateUserView(generics.CreateAPIView):
    """
    View to create user objects.
    """
    permission_classes = (AllowAny, )
    serializer_class = UserCreateRequestSerializer

    def post(self, request, format=None):
        user_create_request = UserCreateRequestSerializer(data=request.data)
        # if the request was invalid
        if not user_create_request.is_valid():
            # throw back an error
            return Response(
                {"status": "error", 
                "data": user_create_request.errors}, 
                status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                # create user and profile objects
                user = User.objects.create_user(
                    email=user_create_request.data['email'],
                    username=user_create_request.data['username'],
                    password=user_create_request.data['password'],
                )
                Profile.objects.create(
                    username=user_create_request.data['username'],
                    first_name=user_create_request.data['first_name'],
                    last_name=user_create_request.data['last_name'],
                    user=user,
                )
                # if we got here, then it was successful
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            # catch failure in process
            except:
                return Response(
                {"status": "error", 
                "data": "Invalid user information."}, 
                status=status.HTTP_400_BAD_REQUEST)
        
    