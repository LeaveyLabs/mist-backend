from datetime import datetime
import random
from django.forms import ValidationError
from rest_framework import serializers
from .models import Flag, Profile, Post, Comment, Message, RegistrationRequest, ValidationRequest, Vote
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('username', 'first_name', 'last_name')

class ValidationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationRequest
        fields = ('email', 'password', 'code_value')
    
    def create(self, data):
        """
        Deserializes new validation object.
        Checks if the code is correct and within time.
        If so, removes the object.
        """
        # parameters
        code_value = data.pop('code_value')
        # 1. validate email
        queryset = ValidationRequest.objects.filter(
            email=data.get('email')).order_by('-code_time')
        if len(queryset) == 0:
            raise ValidationError("Email does not exist.")
        validation = queryset[0]
        registration = validation.registration
        # 2. validate password
        password = data.pop('password')
        if not check_password(password, validation.password):
            raise ValidationError("Passwords do not match.")
        # 3. validate time (more than 5 minutes is invalid)
        curr_time = datetime.now().timestamp()
        if curr_time-validation.code_time > 5*60:
            raise ValidationError("Time limit exceeded.")
        # 4. validate code
        if validation.code_value != code_value:
            raise ValidationError("Code does not match.")
        # produce user object
        user = User(
            email=registration.email,
            username=registration.username,
        )
        user.set_password(password)
        user.save()
        Profile.objects.create(
            username=registration.username,
            first_name=registration.first_name,
            last_name=registration.last_name,
            user=user,
        )
        # delete request objects
        validation.delete()
        registration.delete()
        return validation

class RegisterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationRequest
        fields = ('email', 'username', 'password', 'first_name', 'last_name')
    
    def create(self, validated_data):
        """
        Create a registration request with the registration information.
        Send in a new validation request for the user to validate. 
        """
        password = validated_data.pop('password')
        request = RegistrationRequest(**validated_data)
        request.password = make_password(password)
        request.save()
        code_value = f'{random.randint(0, 999_999):06}'
        ValidationRequest.objects.create(
            email=validated_data.get('email'),
            password=request.password,
            code_value=code_value,
            code_time=datetime.now().timestamp(),
            registration=request,
        )
        send_mail(
            "[Mist] Validate Your Email Address",
            "Your sign-in code is {}".format(code_value),
            "kevinsun127@gmail.com",
            [validated_data.get('email')],
            fail_silently=False,
        )
        return request

class PostSerializer(serializers.ModelSerializer):
    averagerating = serializers.ReadOnlyField(source='calculate_averagerating')
    commentcount = serializers.ReadOnlyField(source='calculate_commentcount')

    class Meta:
        model = Post
        fields = ('id', 'title', 'text', 'location', 'timestamp', 'author', 'averagerating', 'commentcount')

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