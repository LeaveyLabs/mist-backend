import random
from datetime import datetime, timedelta
from django.forms import ValidationError
from rest_framework import serializers
from .models import User, EmailAuthentication
from users.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password

class ReadOnlyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'picture', )

class CompleteUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=50, write_only=True, required=False)

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password',
        'first_name', 'last_name', 'picture', )

    def validate(self, data):
        if 'email' in data:
            # will see if you can register with this email without error
            emailValidator = UserEmailRegistrationSerializer(data=data)
            emailValidator.is_valid()

        if 'password' in data:
            # validates password strength
            password = data.get('password')
            validate_password(password)
        
        return data

    def create(self, validated_data):
        email = validated_data.get('email')
        email_auth_requests = EmailAuthentication.objects.filter(
            email=email).order_by('-validation_time')

        if not email_auth_requests:
            raise serializers.ValidationError({"email": "Email was not registered."})

        most_recent_auth_request = email_auth_requests[0]

        if not most_recent_auth_request.validated:
            raise serializers.ValidationError({"email": "Email was not validated."})

        current_time = datetime.now().timestamp()
        time_since_validation = current_time - most_recent_auth_request.validation_time
        validation_expired = time_since_validation > self.EXPIRATION_TIME

        if validation_expired:
            raise serializers.ValidationError({"email": "Email validation expired."})

        users_with_matching_email = User.objects.filter(email=email)
        if len(users_with_matching_email):
            raise serializers.ValidationError({"email": "Email already taken."})

        username = validated_data.get('username')
        users_with_matching_username = User.objects.filter(username=username)
        
        if len(users_with_matching_username):
            raise serializers.ValidationError({"username": "Username already taken."})
        
        raw_password = validated_data.get('password')
        hashed_password = make_password(raw_password)
        validated_data.update({'password': hashed_password})

        return User.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('username', instance.username)
        instance.set_password(validated_data.get('password', instance.password))
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.picture = validated_data.get('picture', instance.picture)
        instance.save()
        return instance

class UserEmailRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAuthentication
        fields = ('email',)

    ACCEPTABLE_DOMAINS = ('usc.edu', 'gmail.com')
    
    def validate(self, data):
        email = data.get('email')
        domain = email.split('@')[1]
        if domain not in self.ACCEPTABLE_DOMAINS:
            raise ValidationError({"email": "Invalid email domain"})
        return data

class UserEmailValidationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    EXPIRATION_TIME = timedelta(minutes=10).total_seconds()

    def validate(self, data):
        email = data.get('email')
        registrations = EmailAuthentication.objects.filter(
                email=email).order_by('-code_time')

        if not registrations:
            raise ValidationError({"email": "Email was not registered."})

        code = data.get('code')
        registration = registrations[0]
        if code != registration.code:
            raise ValidationError({"code": "Code does not match."})

        current_time = datetime.now().timestamp()
        time_since_registration = current_time - registration.code_time 
        registration_expired = time_since_registration > self.EXPIRATION_TIME

        if registration_expired:
            raise ValidationError({"code": "Code expired (10 minutes)."})

        return data

class UsernameValidationRequestSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, data):
        username = data.get('username')

        if not username:
            raise ValidationError({"username": "Username was not provided."})

        users_with_matching_username = User.objects.filter(username=username)
        if users_with_matching_username:
            raise ValidationError({"username": "Username is not unique."})

        return data