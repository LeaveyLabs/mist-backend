from datetime import datetime
from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from users.generics import get_user_from_request
from users.permissions import UserPermissions
from users.models import User
from django.core.mail import send_mail
from django.db.models import Q

from .serializers import (
    ReadOnlyUserSerializer,
    UserEmailRegistrationSerializer,
    UserEmailValidationRequestSerializer,
    CompleteUserSerializer,
    UsernameValidationRequestSerializer,
)
from .models import (
    User,
    EmailAuthentication,
)

class UserView(viewsets.ModelViewSet):
    permission_classes = (UserPermissions, )
    serializer_class = CompleteUserSerializer

    def get_queryset(self):
        """
        Returns users matching the username, first_name, last_name
        """
        # parameters
        username = self.request.query_params.get('username')
        first_name = self.request.query_params.get('first_name')
        last_name = self.request.query_params.get('last_name')
        text = self.request.query_params.get('text')
        token = self.request.query_params.get('token')
        requesting_user = get_user_from_request(self.request)

        # default is to return all users
        queryset = User.objects.all()
        
        # filter by text...
        if text != None:
            username_set = User.objects.filter(username__contains=text)
            first_name_set = User.objects.filter(first_name__contains=text)
            last_name_set = User.objects.filter(last_name__contains=text)
            queryset = (username_set | first_name_set | last_name_set).distinct()
        # or username, first_name, and last_name
        elif username or first_name or last_name:
            username_set = User.objects.none()
            first_name_set = User.objects.none()
            last_name_set = User.objects.none()
            if username: 
                username_set = User.objects.filter(username__startswith=username)
            if first_name:
                first_name_set = User.objects.filter(first_name__startswith=first_name)
            if last_name:
                last_name_set = User.objects.filter(last_name__startswith=last_name)
            queryset = (username_set | first_name_set | last_name_set).distinct()
        # or token
        elif token:
            matching_tokens = Token.objects.filter(key=token)
            if not matching_tokens: 
                queryset = User.objects.none()
            else:
                matching_token = matching_tokens[0]
                queryset = User.objects.filter(id=matching_token.user.id)

        # set serializers based on requesting user
        if not requesting_user: 
            self.serializer_class = ReadOnlyUserSerializer

        else:
            non_matching_users = ~Q(id=requesting_user.id)
            readonly_users = queryset.filter(non_matching_users)

            if readonly_users:
                self.serializer_class = ReadOnlyUserSerializer
            else:
                self.serializer_class = CompleteUserSerializer

        return queryset

class RegisterUserEmailView(generics.CreateAPIView):
    permission_classes = (AllowAny, )
    serializer_class = UserEmailRegistrationSerializer

    def post(self, request):
        registration_request = UserEmailRegistrationSerializer(data=request.data)
        registration_request.is_valid(raise_exception=True)

        email = registration_request.data.get('email').lower()
        EmailAuthentication.objects.filter(email__iexact=email).delete()
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
    View to validate users emails.
    """
    permission_classes = (AllowAny, )
    serializer_class = UserEmailValidationRequestSerializer

    def post(self, request):
        validation_request = UserEmailValidationRequestSerializer(data=request.data)
        validation_request.is_valid(raise_exception=True)

        registration = EmailAuthentication.objects.filter(
            email__iexact=validation_request.data.get('email').lower()
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

class ValidateUsernameView(generics.CreateAPIView):
    """
    View to validate usersnames
    """
    permission_classes = (AllowAny, )
    serializer_class = UsernameValidationRequestSerializer

    def post(self, request):
        validation_request = UsernameValidationRequestSerializer(data=request.data)
        validation_request.is_valid(raise_exception=True)

        return Response(
            {
                "status": "success",
                "data": validation_request.data,
            },
            status=status.HTTP_200_OK)
