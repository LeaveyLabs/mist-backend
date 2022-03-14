from datetime import datetime
import random
from django.forms import ValidationError
from rest_framework import serializers
from .models import Flag, Profile, Post, Comment, Message, RegistrationRequest, ValidationRequest, Vote, Word
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
    
    def get_request_by_email(self, email):
        matching_email = ValidationRequest.objects.filter(email=email)
        ordered_by_time = matching_email.order_by('-code_time')
        if len(ordered_by_time) == 0: 
            raise serializers.ValidationError("Email does not exist.")
        return ordered_by_time[0]
    
    def validate(self, data):
        # define parameters
        email = data['email']
        password = data['password']
        code_value = data['code_value']
        # validate each parameter:
        # 1. email
        validation = self.get_request_by_email(email)
        # 2. password
        if not check_password(password, validation.password):
            raise serializers.ValidationError("Passwords do not match.")
        # 3. time
        curr_time = datetime.now().timestamp()
        if curr_time-validation.code_time > 5*60:
            raise serializers.ValidationError("Time limit exceeded.")
        # 4. code_value
        if validation.code_value != code_value:
             raise serializers.ValidationError("Code does not match.")
        return data
    
    def create(self, validated_data):
        """
        Deserializes new validation object.
        Checks if the code is correct and within time.
        If so, removes the object.
        """
        # find request by email
        email = validated_data.pop('email')
        request = self.get_request_by_email(email)
        # produce user object
        user = User(
            email=request.registration.email,
            username=request.registration.username,
        )
        user.set_password(request.password)
        user.save()
        # produce profile object
        Profile.objects.create(
            username=request.registration.username,
            first_name=request.registration.first_name,
            last_name=request.registration.last_name,
            user=user,
        )
        # delete request objects
        request.registration.delete()
        request.delete()
        return request

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

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ('text', 'occurrences')

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