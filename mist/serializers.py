from rest_framework import serializers
from .models import Flag, Profile, Post, Comment, Message, Vote
from django.contrib.auth.models import User

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('username', 'first_name', 'last_name')

class PostSerializer(serializers.ModelSerializer):
    trendscore = serializers.ReadOnlyField(source='calculate_trendscore')
    class Meta:
        model = Post
        fields = ('id', 'title', 'text', 'location', 'timestamp', 'author', 'trendscore')

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('voter', 'post', 'timestamp', 'rating')
    
class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ('flagger', 'post', 'timestamp', 'rating') 

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('text', 'timestamp', 'post', 'author')

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('text', 'timestamp', 'from_user', 'to_user')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user