from rest_framework import serializers
from .models import Flag, Post, Comment, Message, Vote, Word

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
    author_picture = serializers.ReadOnlyField(source='author.picture')
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ('id', 'text', 'timestamp', 'post', 'author', 
        'author_picture', 'author_username')

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        if not repr['author_picture']:
            repr.pop('author_picture')
        return repr

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'text', 'timestamp', 'from_user_id', 'to_user_id')