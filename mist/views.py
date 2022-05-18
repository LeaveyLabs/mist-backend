from datetime import datetime
from decimal import Decimal
import random
from django.db.models import Avg, Count
from django.db.models.expressions import RawSQL
from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.core.mail import send_mail

from .serializers import (
    FlagSerializer,
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    ProfileSerializer,
    UserDeletionRequestSerializer,
    UserEmailRegistrationSerializer,
    UserCreationRequestSerializer,
    UserModificationRequestSerializer,
    UserEmailValidationRequestSerializer,
    UserSerializer,
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

class QueryUserView(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        Returns users matching the username, first_name, last_name
        """
        # parameters
        username = self.request.query_params.get('username')
        first_name = self.request.query_params.get('first_name')
        last_name = self.request.query_params.get('last_name')
        text = self.request.query_params.get('text')
        # filter
        if text != None:
            username_set = User.objects.filter(username__contains=text)
            first_name_set = User.objects.filter(first_name__contains=text)
            last_name_set = User.objects.filter(last_name__contains=text)
            return (username_set | first_name_set | last_name_set).distinct()
        else:
            username_set = User.objects.none()
            first_name_set = User.objects.none()
            last_name_set = User.objects.none()
            if username: 
                username_set = User.objects.filter(username__startswith=username)
            if first_name:
                first_name_set = User.objects.filter(first_name__startswith=first_name)
            if last_name:
                last_name_set = User.objects.filter(last_name__startswith=last_name)
            return (username_set | first_name_set | last_name_set).distinct()
            

class DeleteUserView(generics.DestroyAPIView):
    serializer_class = UserDeletionRequestSerializer

    def delete(self, request, *args, **kwargs):
        user_delete_request = UserDeletionRequestSerializer(data=request.data)
        if not user_delete_request.is_valid():
            return Response(
                {
                    "status": "error", 
                    "data": user_delete_request.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        else:
            email = user_delete_request.data['email']
            username = user_delete_request.data['username']
            User.objects.get(email=email, username=username).delete()
            return Response(
                {
                    "status": "success",
                },
                status=status.HTTP_200_OK)

class ModifyUserView(generics.UpdateAPIView):  
    serializer_class = UserModificationRequestSerializer

    def patch(self, request, *args, **kwargs):
        user_modification_request = UserModificationRequestSerializer(data=request.data)
        if not user_modification_request.is_valid():
            return Response(
                {
                    "status": "error", 
                    "data": user_modification_request.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        else:
            email = user_modification_request.data['email']
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)

            if 'username' in user_modification_request.data:
                username = user_modification_request.data['username']
                user.username = username

            if 'password' in user_modification_request.data:
                password = user_modification_request.data['password']
                user.set_password(password)

            if 'first_name' in user_modification_request.data:
                first_name = user_modification_request.data['first_name']
                user.first_name = first_name

            if 'last_name' in user_modification_request.data:
                last_name = user_modification_request.data['last_name']
                user.last_name = last_name
            
            user.save()
            profile.save()

            return Response(
                {
                    "status": "success",
                    "data": UserSerializer(user).data
                },
                status=status.HTTP_200_OK)

class ProfileView(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        username = self.request.query_params.get('username')
        if username == None: 
            return Profile.objects.none()
        else: 
            try:
                user = User.objects.get(username=username)
                return Profile.objects.filter(user=user)
            except:
                return Profile.objects.none()

class PostView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    # Max distance around post is 1 kilometer
    MAX_DISTANCE = Decimal(1)

    def get_locations_nearby_coords(self, latitude, longitude, max_distance=None):
        """
        Return objects sorted by distance to specified coordinates
        which distance is less than max_distance given in kilometers
        """
        # Great circle distance formula
        gcd_formula = "6371 * acos(least(greatest(\
        cos(radians(%s)) * cos(radians(latitude)) \
        * cos(radians(longitude) - radians(%s)) + \
        sin(radians(%s)) * sin(radians(latitude)) \
        , -1), 1))"
        distance_raw_sql = RawSQL(
            gcd_formula,
            (latitude, longitude, latitude)
        )
        # make sure the latitude + longtitude exists
        # make sure the distance is under the max
        qs = Post.objects.all()\
        .filter(latitude__isnull=False)\
        .filter(longitude__isnull=False)\
        .annotate(distance=distance_raw_sql)\
        .order_by('distance')
        if max_distance is not None:
            # distance must be less than max distance
            qs = qs.filter(distance__lt=max_distance)
        return qs

    def get_queryset(self):
        """
        Filter by text, location, and date. 
        If a parameter does not exist, then skip it. 
        Sort the result by vote ratings. 
        """
        # parameters
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        text = self.request.query_params.get('text')
        timestamp = self.request.query_params.get('timestamp')
        location_description = self.request.query_params.get('location_description')
        # filter
        queryset = Post.objects.all()
        if latitude != None and longitude != None:
            queryset = self.get_locations_nearby_coords(
                latitude, longitude, max_distance=self.MAX_DISTANCE)
        if text != None:
            text_set = queryset.filter(text__contains=text)
            title_set = queryset.filter(title__contains=text)
            queryset = (text_set | title_set).distinct()
        if timestamp != None:
            queryset = queryset.filter(timestamp=timestamp)
        if location_description != None:
            loc_set = queryset.filter(location_description__isnull=False)
            queryset = loc_set.filter(
                location_description__contains=location_description)
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
        return Word.objects.filter(text__contains=text
        ).annotate(post_count=Count('posts')
        ).filter(post_count__gt=0)

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
            matching_users = User.objects.filter(username=username)
            if not matching_users: return Vote.objects.none()
            return Vote.objects.filter(voter=matching_users[0], post_id=post_id)

class FlagView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = FlagSerializer
    queryset = Vote.objects.all()

class MessageView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

class RegisterUserEmailView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = UserEmailRegistrationSerializer

    def post(self, request, format=None):
        registration_request = UserEmailRegistrationSerializer(data=request.data)
        if not registration_request.is_valid():
            # return error
            return Response(
                {
                    "status": "error", 
                    "data": registration_request.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        else:
            email = registration_request.data['email']
            rand_code = f'{random.randint(0, 999_999):06}'
            curr_time = datetime.now().timestamp()
            request = Registration.objects.create(
                email=email,
                code=rand_code,
                code_time=curr_time,
            )
            send_mail(
                "Your code awaits!",
                "Here's your validation code: {}".format(rand_code),
                "getmist.app@gmail.com",
                [email],
                fail_silently=False,
            )
            return Response(
                {
                    "status": "success",
                    "data": registration_request.data,
                }, 
                status=status.HTTP_201_CREATED)

class ValidateUserEmailView(generics.CreateAPIView):
    """
    View to validate users. 
    """
    permission_classes = (AllowAny, )
    serializer_class = UserEmailValidationRequestSerializer

    def post(self, request, format=None):
        # check validation request
        validation = UserEmailValidationRequestSerializer(data=request.data)
        # if the data is not valid
        if not validation.is_valid():
            # return error
            return Response(
                {
                    "status": "error", 
                    "data": validation.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        # if the data is valid
        else:
            # mark registration as validated
            registration = Registration.objects.filter(
                email=validation.data['email']
                ).order_by('-code_time')[0]
            registration.validated = True
            registration.validation_time = datetime.now().timestamp()
            registration.save()
            return Response(
                {
                    "status": "success"
                }, 
                status=status.HTTP_200_OK)

class CreateUserView(generics.CreateAPIView):
    """
    View to create user objects.
    """
    permission_classes = (AllowAny, )
    serializer_class = UserCreationRequestSerializer

    def post(self, request, format=None):
        user_create_request = UserCreationRequestSerializer(data=request.data)
        # if the request was invalid
        if not user_create_request.is_valid():
            # throw back an error
            return Response(
                {
                    "status": "error", 
                    "data": user_create_request.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                # create user and profile objects
                user = User.objects.create_user(
                    email=user_create_request.data['email'],
                    username=user_create_request.data['username'],
                    password=user_create_request.data['password'],
                    first_name=user_create_request.data['first_name'],
                    last_name=user_create_request.data['last_name'],
                )
                Profile.objects.create(
                    user=user,
                )
                # if we got here, then it was successful
                return Response(
                    {
                        "status": "success"
                    }, 
                    status=status.HTTP_200_OK)
            # catch failure in process
            except:
                return Response(
                {
                    "status": "error", 
                    "data": "Invalid user information."
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        
    