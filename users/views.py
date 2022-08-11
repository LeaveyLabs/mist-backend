from datetime import datetime
import os
from rest_framework import viewsets, generics
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from twilio.rest import Client
from users.generics import get_current_time, get_user_from_request, get_random_code
from users.permissions import UserPermissions
from django.core.mail import send_mail
from django.db.models import Q
from django.db.models.expressions import RawSQL

from .serializers import (
    LoginCodeRequestSerializer,
    LoginSerializer,
    PasswordResetFinalizationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetValidationSerializer,
    PasswordValidationRequestSerializer,
    PhoneNumberRegistrationSerializer,
    ResetEmailValidationSerializer,
    ResetTextRequestSerializer,
    ResetEmailRequestSerializer,
    PhoneNumberValidationSerializer,
    ReadOnlyUserSerializer,
    ResetTextValidationSerializer,
    UserEmailRegistrationSerializer,
    UserEmailValidationRequestSerializer,
    CompleteUserSerializer,
    UsernameValidationRequestSerializer,
)
from .models import (
    PasswordReset,
    PhoneNumberAuthentication,
    PhoneNumberReset,
    User,
    EmailAuthentication,
)


# Twilio Initialization
environment = os.getenv('ENVIRONMENT')

class TwilioTestClient:

    def __init__(self, sid, token):
        self.sid = sid
        self.token = token
        self.messages = TwillioTestClientMessages()

class TwillioTestClientMessages:

    created = []

    def create(self, to, from_, body):
        self.created.append({
            'to': to,
            'from_': from_,
            'body': body
        })

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_phone_number = os.environ['TWILIO_PHONE_NUMBER']

if environment == 'dev':
    twilio_client = TwilioTestClient(account_sid, auth_token)
else:
    twilio_client = Client(account_sid, auth_token)


# Views
class UserView(viewsets.ModelViewSet):
    permission_classes = (UserPermissions, )
    serializer_class = CompleteUserSerializer

    def get_object(self):
        requested_user = super().get_object()
        requesting_user = get_user_from_request(self.request)
        if requesting_user == requested_user:
            self.serializer_class = CompleteUserSerializer
        return requested_user

    def get_queryset(self):
        """
        Returns users matching the username, first_name, last_name
        """
        # parameters
        username = self.request.query_params.get('username')
        first_name = self.request.query_params.get('first_name')
        last_name = self.request.query_params.get('last_name')
        words = self.request.query_params.getlist('words')
        token = self.request.query_params.get('token')
        phone_numbers = self.request.query_params.getlist('phone_numbers')
        requesting_user = get_user_from_request(self.request)

        # default is to return all users
        queryset = User.objects.all()

        # filter by words...
        if words:
            for word in words:
                word_in_username = User.objects.filter(username__icontains=word)
                word_in_first_name = User.objects.filter(first_name__icontains=word)
                word_in_last_name = User.objects.filter(last_name__icontains=word)
                word_userset = (word_in_username | word_in_first_name | word_in_last_name).distinct()
                queryset = queryset.intersection(word_userset)
            queryset = User.objects.filter(id__in=queryset.values_list('id'))
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
        # or phone_number
        elif phone_numbers:
            queryset = User.objects.filter(phone_number__in=phone_numbers)
        # or token
        elif token:
            matching_tokens = Token.objects.filter(key=token)
            if not matching_tokens:
                queryset = User.objects.none()
            else:
                matching_token = matching_tokens[0]
                queryset = User.objects.filter(id=matching_token.user.id)

        # set serializers based on requesting user + method
        object_level_methods = ["DELETE", "PUT", "PATCH",]
        if self.request.method in object_level_methods:
            return queryset
        else:
            non_matching_users = ~Q(id=requesting_user.id)
            readonly_users = queryset.filter(non_matching_users)

            if readonly_users:
                self.serializer_class = ReadOnlyUserSerializer
            else:
                self.serializer_class = CompleteUserSerializer

        return queryset

class NearbyUsersView(generics.ListAPIView):
    permission_classes = (UserPermissions, )
    serializer_class = ReadOnlyUserSerializer

    MAX_DISTANCE = .1

    def get_locations_nearby_coords(self, latitude, longitude, max_distance=MAX_DISTANCE):
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
        qs = User.objects.all()\
        .filter(latitude__isnull=False)\
        .filter(longitude__isnull=False)\
        .annotate(distance=distance_raw_sql)\
        .order_by('distance')
        # distance must be less than max distance
        qs = qs.filter(distance__lt=max_distance)
        return qs

    def get_queryset(self):
        requesting_user = get_user_from_request(self.request)
        nearby_users = self.get_locations_nearby_coords(
            requesting_user.latitude,
            requesting_user.longitude)
        return nearby_users

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

class ValidatePasswordView(generics.CreateAPIView):
    """
    View to validate password
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordValidationRequestSerializer
    
    def post(self, request):
        validation_request = PasswordValidationRequestSerializer(data=request.data)
        validation_request.is_valid(raise_exception=True)

        return Response(
            {
                "status": "success",
                "data": validation_request.data,
            },
            status=status.HTTP_201_CREATED)

class LoginView(generics.CreateAPIView):
    """
    View to login
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        content = {
            'token': token.key,
        }

        return Response(content)

class RequestPasswordResetView(generics.CreateAPIView):
    """
    View to request password resets
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        password_reset_request = PasswordResetRequestSerializer(data=request.data)
        password_reset_request.is_valid(raise_exception=True)

        email = password_reset_request.data.get('email').lower()
        PasswordReset.objects.filter(email__iexact=email).delete()
        password_reset = PasswordReset.objects.create(email=email)

        send_mail(
            "Reset your password!",
            "Here's your code: {}".format(password_reset.code),
            "getmist.app@gmail.com",
            [email],
            fail_silently=False,
        )
        
        return Response(
            {
                "status": "success",
                "data": password_reset_request.data,
            }, 
            status=status.HTTP_201_CREATED)

class ValidatePasswordResetView(generics.CreateAPIView):
    """
    View to validate password resets
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordResetValidationSerializer
    
    def post(self, request):
        password_reset_validation = PasswordResetValidationSerializer(data=request.data)
        password_reset_validation.is_valid(raise_exception=True)

        email = password_reset_validation.data.get('email')
        code = password_reset_validation.data.get('code')
        password_reset = PasswordReset.objects.filter(
            email__iexact=email.lower(),
            code=code,
            ).order_by('-code_time')[0]
        password_reset.validated = True
        password_reset.validation_time = datetime.now().timestamp()
        password_reset.save()

        return Response(
            {
                "status": "success",
                "data": password_reset_validation.data,
            }, 
            status=status.HTTP_200_OK)

class FinalizePasswordResetView(generics.CreateAPIView):
    """
    View to finalize password resets
    """
    permission_classes = (AllowAny, )
    serializer_class = PasswordResetFinalizationSerializer
    
    def post(self, request):
        password_reset_finalization = PasswordResetFinalizationSerializer(data=request.data)
        password_reset_finalization.is_valid(raise_exception=True)

        email = password_reset_finalization.data.get('email')
        password = password_reset_finalization.data.get('password')

        requesting_user = User.objects.get(email=email)
        requesting_user.set_password(password)
        requesting_user.save()

        return Response(
            {
                "status": "success",
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
        phone_number_authentication = PhoneNumberAuthentication.objects.create(
            email=email, phone_number=phone_number)

        twilio_client.messages.create(
            body=f"Your verification code for Mist is {phone_number_authentication.code}",
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

class RequestLoginCodeView(generics.CreateAPIView):
    """
    View to request login code to phone number
    """
    
    def post(self, request, *args, **kwargs):
        login_request = LoginCodeRequestSerializer(data=request.data)
        login_request.is_valid(raise_exception=True)
        phone_number = login_request.data.get('phone_number')

        phone_number_authentication = PhoneNumberAuthentication.objects.get(
            phone_number=phone_number)
        phone_number_authentication.code = get_random_code()
        phone_number_authentication.code_time = get_current_time()
        phone_number_authentication.save()

        twilio_client.messages.create(
            body=f"Your verification code for Mist is {phone_number_authentication.code}",
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
            "Reset your phone number!",
            f"Here's your code: {phone_number_reset.email_code}",
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
