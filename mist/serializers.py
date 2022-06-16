from rest_framework import serializers
from .models import Block, Favorite, Feature, Flag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, Vote, Word

class WordSerializer(serializers.ModelSerializer):
    occurrences = serializers.ReadOnlyField(source='calculate_occurrences')

    class Meta:
        model = Word
        fields = ('id', 'text', 'occurrences')

class PostSerializer(serializers.ModelSerializer):
    averagerating = serializers.ReadOnlyField(source='calculate_averagerating')
    commentcount = serializers.ReadOnlyField(source='calculate_commentcount')

    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'averagerating', 'commentcount', )

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
    author_picture = serializers.ReadOnlyField(source='author.picture')
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ('id', 'body', 'timestamp', 'post', 'author', 
        'author_picture', 'author_username')

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        pic = repr.pop('author_picture')
        if pic: repr['author_picture'] = pic.url
        return repr

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