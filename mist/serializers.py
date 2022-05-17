import random
from datetime import datetime, timedelta
from django.forms import ValidationError
from rest_framework import serializers
from .models import Flag, Profile, Post, Comment, Message, Registration, Vote, Word
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'picture' )

    def get_picture(self, obj):
        return Profile.objects.get(user=obj.pk).picture

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

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
            Profile.objects.get(user=user)
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
        registrations = Registration.objects.filter(
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
        registrations = Registration.objects.filter(
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
        model = Registration
        fields = ('email',)

    ACCEPTABLE_DOMAINS = ('usc.edu', 'gmail.com')
    
    def validate(self, data):
        # domain must be in the list
        email = data['email']
        domain = email.split('@')[1]
        if domain not in self.ACCEPTABLE_DOMAINS:
            raise ValidationError("Invalid email domain")
        return data
    
    def create(self, validated_data):
        """
        Create a registration request with the registration information.
        """
        # parameters
        email = validated_data.get('email')
        rand_code = f'{random.randint(0, 999_999):06}'
        curr_time = datetime.now().timestamp()
        # create request
        request = Registration.objects.create(
            email=email,
            code=rand_code,
            code_time=curr_time,
        )
        # send validation email
        send_mail(
            "Your code awaits!",
            "Here's your validation code: {}".format(rand_code),
            "getmist.app@gmail.com",
            [email],
            fail_silently=False,
        )
        return request

class WordSerializer(serializers.ModelSerializer):
    occurrences = serializers.ReadOnlyField(source='calculate_occurrences')

    class Meta:
        model = Word
        fields = ('text', 'occurrences')

class PostSerializer(serializers.ModelSerializer):
    averagerating = serializers.ReadOnlyField(source='calculate_averagerating')
    commentcount = serializers.ReadOnlyField(source='calculate_commentcount')

    class Meta:
        model = Post
        fields = ('id', 'uuid', 'title', 'text', 'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'averagerating', 'commentcount', )

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('id', 'voter', 'post', 'timestamp', 'rating')
    
class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ('id', 'flagger', 'post', 'timestamp', 'rating') 

class CommentSerializer(serializers.ModelSerializer):
    author_picture = serializers.SerializerMethodField()
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'text', 'timestamp', 'post', 
        'author', 'author_picture', 'author_username')

    def get_author_picture(self, obj):
        return Profile.objects.get(user=obj.author_id).picture
    
    def get_author_username(self, obj):
        return User.objects.get(pk=obj.author_id).username


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'text', 'timestamp', 'from_user', 'to_user')