import random
from datetime import datetime, timedelta
from django.forms import ValidationError
from rest_framework import serializers
from .models import Flag, Profile, Post, Comment, Message, Registration, Vote, Word
from django.core.mail import send_mail

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('username', 'first_name', 'last_name', 'picture', 'user')

class UserCreateRequestSerializer(serializers.Serializer):
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

class ValidationSerializer(serializers.Serializer):
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

class RegistrationSerializer(serializers.ModelSerializer):
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
            "[Mist] Validate Your Email Address",
            "Your sign-in code is {}".format(rand_code),
            "kevinsun127@gmail.com",
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
        fields = ('id', 'title', 'text', 'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'averagerating', 'commentcount', )

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('id', 'voter', 'post', 'timestamp', 'rating')
    
class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ('flagger', 'post', 'timestamp', 'rating') 

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'text', 'timestamp', 'post', 'author')

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('text', 'timestamp', 'from_user', 'to_user')