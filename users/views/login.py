import os
from rest_framework import generics
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from users.generics import get_current_time, get_random_code

import sys
sys.path.append("..")
from twilio_config import twilio_client, twilio_phone_number

from ..serializers import (
    LoginCodeRequestSerializer,
    PhoneNumberValidationSerializer
)
from ..models import (
    PhoneNumberAuthentication,
    User,
)


class RequestLoginCodeView(generics.CreateAPIView):
    """
    View to request login code to phone number
    """
    DEFAULT_CODE = "123456"

    backdoor_usernames = [
        "mist",
        "corylevy",
    ]
    
    def is_testing_admin(self, phone_number):
        users_with_matching_phone_number = User.objects.filter(phone_number=phone_number)
        testing_admin_users = User.objects.filter(username__in=self.backdoor_usernames)
        if not users_with_matching_phone_number.exists(): return False
        if not testing_admin_users.exists(): return False
        return users_with_matching_phone_number[0] == testing_admin_users[0]

    def login_backdoor_enabled(self):
        return os.environ.get('ENVIRONMENT') == 'dev' or os.environ.get('ENVIRONMENT') == 'local'
    
    def post(self, request, *args, **kwargs):
        login_request = LoginCodeRequestSerializer(data=request.data)
        login_request.is_valid(raise_exception=True)
        phone_number = login_request.data.get('phone_number')

        phone_number_authentications = PhoneNumberAuthentication.objects.filter(
            phone_number=phone_number)
        if not phone_number_authentications:
            phone_number_authentications = [
                PhoneNumberAuthentication.objects.create(phone_number=phone_number)
            ]
        phone_number_authentication = phone_number_authentications[0]
        phone_number_authentication.code = get_random_code()
        phone_number_authentication.code_time = get_current_time()
        phone_number_authentication.save()

        # if self.login_backdoor_enabled() and self.is_testing_admin(phone_number):
        if self.is_testing_admin(phone_number):
            phone_number_authentication.code = self.DEFAULT_CODE
            phone_number_authentication.save()

        twilio_client.messages.create(
            body=f"your verification code for mist is {phone_number_authentication.code}",
            from_=twilio_phone_number,
            to=str(phone_number_authentication.phone_number),
        )

        return Response(
            {
                "status": "success",
                "data": login_request.data,
            },
            status=status.HTTP_200_OK)


class ValidateLoginCodeView(generics.CreateAPIView):
    """
    View to validate login code sent to phone number
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
        authentication.code = get_random_code()
        authentication.code_time = 0
        authentication.validated = True
        authentication.validation_time = get_current_time()
        authentication.save()

        user = User.objects.get(phone_number=phone_number)
        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
            },
            status=status.HTTP_200_OK)
