from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from users.generics import get_current_time, get_random_code
from django.core.mail import send_mail

import sys
sys.path.append("..")
from twilio_config import twilio_client, twilio_phone_number

from ..serializers import (
    ResetEmailValidationSerializer,
    ResetTextRequestSerializer,
    ResetEmailRequestSerializer,
    ResetTextValidationSerializer
)
from ..models import (
    PhoneNumberReset,
    User,
)


class RequestResetEmailView(generics.CreateAPIView):
    """
    View to request reset phone number
    """
    def post(self, request, *args, **kwargs):
        reset_request = ResetEmailRequestSerializer(data=request.data)
        reset_request.is_valid(raise_exception=True)
        email = reset_request.data.get('email').lower()

        PhoneNumberReset.objects.filter(email__iexact=email).delete()
        phone_number_reset = PhoneNumberReset.objects.create(email=email)

        send_mail(
            "Reset your phone number",
            f"Your email verification code for Mist is {phone_number_reset.email_code}",
            "getmist.app@gmail.com",
            [email],
            fail_silently=False,
        )
        
        return Response(
            {
                "status": "success",
                "data": reset_request.data,
            }, 
            status=status.HTTP_201_CREATED)


class ValidateResetEmailView(generics.CreateAPIView):
    """
    View to validate email used to reset phone number
    """
    def post(self, request, *args, **kwargs):
        validation = ResetEmailValidationSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        email = validation.data.get('email').lower()
        code = validation.data.get('code')

        phone_number_reset = PhoneNumberReset.objects.get(
            email__iexact=email,
            email_code=code,
        )
        phone_number_reset.email_validated = True
        phone_number_reset.email_validation_time = get_current_time()
        phone_number_reset.reset_token = get_random_code()
        phone_number_reset.save()

        return Response(
            {
                "status": "success",
                "token": phone_number_reset.reset_token,
            },
            status=status.HTTP_200_OK)


class RequestResetTextCodeView(generics.CreateAPIView):
    """
    View to register a new phone number for an email
    """
    def post(self, request, *args, **kwargs):
        registration = ResetTextRequestSerializer(data=request.data)
        registration.is_valid(raise_exception=True)
        email = registration.data.get('email').lower()
        phone_number = registration.data.get('phone_number')

        phone_number_reset = PhoneNumberReset.objects.get(
            email__iexact=email,
        )
        phone_number_reset.phone_number = phone_number
        phone_number_reset.phone_number_code = get_random_code()
        phone_number_reset.phone_number_code_time = get_current_time()
        phone_number_reset.save()

        twilio_client.messages.create(
            body=f"Your verification code for Mist is {phone_number_reset.phone_number_code}",
            from_=twilio_phone_number,
            to=str(phone_number_reset.phone_number),
        )

        return Response(
            {
                "status": "success",
                "data": registration.data,
            },
            status=status.HTTP_200_OK)


class ValidateResetTextCodeView(generics.CreateAPIView):
    """
    View to validate reset phone number with code
    """
    def post(self, request, *args, **kwargs):
        validation = ResetTextValidationSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        phone_number = validation.data.get('phone_number')
        code = validation.data.get('code')

        phone_number_reset = PhoneNumberReset.objects.get(
            phone_number=phone_number,
            phone_number_code=code,
        )
        phone_number_reset.phone_number_validated = True
        phone_number_reset.phone_number_validation_time = get_current_time()
        phone_number_reset.save()

        user_email = phone_number_reset.email
        user = User.objects.get(email=user_email)
        user.phone_number = phone_number
        user.save()
        
        return Response(
            {
                "status": "success",
                "data": validation.data,
            },
            status=status.HTTP_200_OK)