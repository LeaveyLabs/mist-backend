from rest_framework import serializers
from users.models import User

from users.serializers import ReadOnlyUserSerializer
from .models import Block, CommentFlag, CommentVote, Favorite, Feature, PostFlag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, PostVote, Word

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
    votes = serializers.SerializerMethodField()

    votecount = serializers.ReadOnlyField(source='calculate_votecount')
    averagerating = serializers.ReadOnlyField(source='calculate_averagerating')
    commentcount = serializers.ReadOnlyField(source='calculate_commentcount')
    flagcount = serializers.ReadOnlyField(source='calculate_flagcount')

    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'averagerating', 'commentcount', 'votecount', 'flagcount', 
        'read_only_author', 'votes', )
    
    def get_read_only_author(self, obj):
        author_pk = obj.author.pk
        author_instance = User.objects.get(pk=author_pk)
        return ReadOnlyUserSerializer(author_instance).data
    
    def get_votes(self, obj):
        vote_instances = PostVote.objects.filter(post_id=obj.id)
        votes_data = []
        for vote_instance in vote_instances:
            votes_data.append(PostVoteSerializer(vote_instance).data)
        return votes_data

class PostVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVote
        fields = ('id', 'voter', 'post', 'timestamp', 'rating', 'emoji',)
    
class PostFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFlag
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
    read_only_post = serializers.SerializerMethodField()

    class Meta:
        model = MatchRequest
        fields = ('id', 'match_requesting_user', 'match_requested_user', 'post', 'read_only_post', 'timestamp')

    def get_read_only_post(self, obj):
        if not obj.post: return None
        post_pk = obj.post.pk
        post_instance = Post.objects.get(pk=post_pk)
        return PostSerializer(post_instance).data

class CommentSerializer(serializers.ModelSerializer):
    read_only_author = serializers.SerializerMethodField()
    votecount = serializers.ReadOnlyField(source='calculate_votecount')
    flagcount = serializers.ReadOnlyField(source='calculate_flagcount')

    class Meta:
        model = Comment
        fields = ('id', 'body', 'timestamp', 
        'post', 'author', 'read_only_author',
        'votecount', 'flagcount',)

    def get_read_only_author(self, obj):
        author_pk = obj.author.pk
        author_instance = User.objects.get(pk=author_pk)
        return ReadOnlyUserSerializer(author_instance).data

class CommentVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentVote
        fields = ('id', 'voter', 'comment', 'timestamp', 'rating')
    
class CommentFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentFlag
        fields = ('id', 'flagger', 'comment', 'timestamp', 'rating')

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