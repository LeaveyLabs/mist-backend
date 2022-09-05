from datetime import datetime
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail

import sys
sys.path.append("..")
from twilio_config import twilio_client, twilio_phone_number

from ..serializers import (
    PhoneNumberRegistrationSerializer,
    PhoneNumberValidationSerializer,
    UserEmailRegistrationSerializer,
    UserEmailValidationRequestSerializer,
    UsernameValidationRequestSerializer,
)
from ..models import (
    EmailAuthentication,
    PhoneNumberAuthentication,
)


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
            "Your code awaits",
            f"Your email verification code for Mist is {email_auth.code}",
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
            email__iexact=validation_request.data.get('email').lower(),
            code=validation_request.data.get('code'),
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


class RegisterPhoneNumberView(generics.CreateAPIView):
    """
    View to register phone numbers
    """
    
    def post(self, request, *args, **kwargs):
        phone_number_registration = PhoneNumberRegistrationSerializer(data=request.data)
        phone_number_registration.is_valid(raise_exception=True)
        phone_number = phone_number_registration.data.get('phone_number')
        email = phone_number_registration.data.get('email').lower()

        PhoneNumberAuthentication.objects.filter(email__iexact=email).delete()
        PhoneNumberAuthentication.objects.filter(phone_number=phone_number).delete()
        phone_number_authentication = PhoneNumberAuthentication.objects.create(
            email=email, phone_number=phone_number)

        twilio_client.messages.create(
            body=f"Your phone number verification code for Mist is {phone_number_authentication.code}",
            from_=twilio_phone_number,
            to=str(phone_number_authentication.phone_number),
        )

        return Response(
            {
                "status": "success",
                "data": phone_number_registration.data,
            },
            status=status.HTTP_201_CREATED)


class ValidatePhoneNumberView(generics.CreateAPIView):
    """
    View to validate phone numbers
    """
    
    def post(self, request, *args, **kwargs):
        validation = PhoneNumberValidationSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        phone_number = validation.data.get('phone_number')
        code = validation.data.get('code')

        authentication = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number,
            code=code,
        ).order_by('-code_time')[0]
        authentication.validated = True
        authentication.validation_time = datetime.now().timestamp()
        authentication.save()

        return Response(
            {
                "status": "success",
                "data": validation.data,
            },
            status=status.HTTP_200_OK)
