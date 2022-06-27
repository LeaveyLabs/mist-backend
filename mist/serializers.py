from rest_framework import serializers
from users.models import User

from users.serializers import ReadOnlyUserSerializer
from .models import Block, Favorite, Feature, Flag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, Vote, Word

class WordSerializer(serializers.ModelSerializer):
    occurrences = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ('id', 'text', 'occurrences')
    
    def get_occurrences(self, obj):
        if obj.occurrences != None: return obj.occurrences
        return obj.calculate_occurrences()

class PostSerializer(serializers.ModelSerializer):
    read_only_author = serializers.SerializerMethodField()
    votecount = serializers.ReadOnlyField(source='calculate_votecount')
    averagerating = serializers.ReadOnlyField(source='calculate_averagerating')
    commentcount = serializers.ReadOnlyField(source='calculate_commentcount')
    flagcount = serializers.ReadOnlyField(source='calculate_flagcount')

    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'averagerating', 'commentcount', 'votecount', 'flagcount', 'read_only_author')
    
    def get_read_only_author(self, obj):
        author_pk = obj.author.pk
        author_instance = User.objects.get(pk=author_pk)
        return ReadOnlyUserSerializer(author_instance).data

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('id', 'voter', 'post', 'timestamp', 'rating')
    
class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ('id', 'flagger', 'post', 'timestamp', 'rating')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'post', 'tagged_user', 'tagging_user', 'timestamp')

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ('id', 'blocked_user', 'blocking_user', 'timestamp')

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ('id', 'friend_requesting_user', 'friend_requested_user', 'timestamp')

class MatchRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchRequest
        fields = ('id', 'match_requesting_user', 'match_requested_user', 'post', 'timestamp')

class CommentSerializer(serializers.ModelSerializer):
    read_only_author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'body', 'timestamp', 'post', 'author', 'read_only_author')

    def get_read_only_author(self, obj):
        author_pk = obj.author.pk
        author_instance = User.objects.get(pk=author_pk)
        return ReadOnlyUserSerializer(author_instance).data

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'body', 'timestamp', 'sender', 'receiver', 'post')
    
class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'timestamp', 'post', 'favoriting_user')

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'timestamp', 'post')