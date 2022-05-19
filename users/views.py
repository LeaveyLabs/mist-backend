from datetime import datetime
from decimal import Decimal
import random
from django.db.models import Avg, Count
from django.db.models.expressions import RawSQL
from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from users.models import User
from django.core.mail import send_mail

from .serializers import (
    UserDeletionRequestSerializer,
    UserEmailRegistrationSerializer,
    UserCreationRequestSerializer,
    UserModificationRequestSerializer,
    UserEmailValidationRequestSerializer,
    UserSerializer,
)
from .models import (
    User,
    EmailAuthentication,
)

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
            EmailAuthentication.objects.create(
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
            registration = EmailAuthentication.objects.filter(
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

            return Response(
                {
                    "status": "success",
                    "data": UserSerializer(user).data
                },
                status=status.HTTP_200_OK)