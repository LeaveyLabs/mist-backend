import random
from datetime import datetime, timedelta
from django.forms import ValidationError
from rest_framework import serializers
from .models import User, EmailAuthentication
from users.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 
        'first_name', 'last_name', 'picture', )
        
class UserDeletionRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=30)

    def validate(self, data):
        email = data['email']
        username = data['username']
        password = data['password']
        try:
            user = User.objects.get(email=email, username=username)
        except:
            raise ValidationError('Email-Username-Password combination does not exist.')

        user = authenticate(email=email, username=username, password=password)
        if not user: 
            raise ValidationError("Invalid User Credentials.")
        return data

class UserModificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=30, required=False)
    password = serializers.CharField(max_length=30, required=False)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)

    def validate(self, data):
        email = data['email']
        try:
            user = User.objects.get(email=email)
        except:
            raise ValidationError('User does not exist.')
    
        if 'username' in data:
            username = data['username']
            matching_users = User.objects.filter(username=username)
            if matching_users:
                raise ValidationError('Username is already in use.')
        
        if 'password' in data:
            password = data['password']
            validate_password(password, user=user)
        
        return data

class UserCreationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=30)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        # parameters
        email = data['email']
        curr_time = datetime.now().timestamp()
        registrations = EmailAuthentication.objects.filter(
            email=email).order_by('-validation_time')
        # registration exists
        if not registrations: 
            raise ValidationError("Email was not registered.")
        registration = registrations[0]
        # registration was validated
        if not registration.validated:
            raise ValidationError("Email was not validated.")
        # validation has not expired
        if curr_time-registration.validation_time > self.EXPIRATION_TIME:
            raise ValidationError("Validation time expired.")
        return data

class UserEmailValidationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        # parameters
        email = data['email']
        code = data['code']
        time = datetime.now().timestamp()
        registrations = EmailAuthentication.objects.filter(
                email=email).order_by('-code_time')
        # validate email
        if not registrations:
            raise ValidationError("Email was not registered.")
        # validate code
        registration = registrations[0]
        if code != registration.code:
            raise ValidationError("Code does not match.")
        # validate code time
        if time-registration.code_time > self.EXPIRATION_TIME:
            raise ValidationError("Code expired (5 minutes).")
        return data

class UserEmailRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAuthentication
        fields = ('email',)

    ACCEPTABLE_DOMAINS = ('usc.edu', 'gmail.com')
    
    def validate(self, data):
        # domain must be in the list
        email = data['email']
        domain = email.split('@')[1]
        if domain not in self.ACCEPTABLE_DOMAINS:
            raise ValidationError("Invalid email domain")
        return data