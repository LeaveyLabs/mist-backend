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
    UserEmailRegistrationSerializer,
    UserEmailValidationRequestSerializer,
    UserSerializer,
)
from .models import (
    User,
    EmailAuthentication,
)

class UserView(viewsets.ModelViewSet):
    permission_classes = (AllowAny, )
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

        # if no filter parameters, return everything
        if (username == None and first_name == None and 
            last_name == None and text == None):
            return User.objects.all()

        # filter by text...
        if text != None:
            username_set = User.objects.filter(username__contains=text)
            first_name_set = User.objects.filter(first_name__contains=text)
            last_name_set = User.objects.filter(last_name__contains=text)
            return (username_set | first_name_set | last_name_set).distinct()
        # or username, first_name, and last_name
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

class RegisterUserEmailView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = UserEmailRegistrationSerializer

    def post(self, request):
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
            email_auth = EmailAuthentication.objects.create(email=email)
            send_mail(
                "Your code awaits!",
                "Here's your validation code: {}".format(email_auth.code),
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

    def post(self, request):
        # check validation request
        validation_request = UserEmailValidationRequestSerializer(data=request.data)
        # if the data is not valid
        if not validation_request.is_valid():
            # return error
            return Response(
                {
                    "status": "error", 
                    "data": validation_request.errors
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        # if the data is valid
        else:
            # mark registration as validated
            registration = EmailAuthentication.objects.filter(
                email=validation_request.data['email']
                ).order_by('-code_time')[0]
            registration.validated = True
            registration.validation_time = datetime.now().timestamp()
            registration.save()
            return Response(
                {
                    "status": "success",
                    "data": validation_request.data,
                }, 
                status=status.HTTP_200_OK)