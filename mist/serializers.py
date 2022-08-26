from psycopg2 import IntegrityError
from profanity_check import predict
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
        return ReadOnlyUserSerializer(obj.author).data
    
    def get_votes(self, obj):
        vote_instances = PostVote.objects.filter(post_id=obj.id)
        votes_data = []
        for vote_instance in vote_instances:
            votes_data.append(PostVoteSerializer(vote_instance).data)
        return votes_data

    def validate_body(self, body):
        [is_offensive] = predict([body])
        if is_offensive:
            raise serializers.ValidationError("Avoid offensive language.")
        return body

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
        fields = ('id', 'comment', 'tagged_name', 'tagged_phone_number',
        'tagged_user', 'tagging_user', 'timestamp')
        extra_kwargs = {
            'tagged_phone_number': {'required': False},
            'tagged_user': {'required': False},
        }
    
    def validate(self, data):
        tagged_phone_number = data.get('tagged_phone_number')
        tagged_user = data.get('tagged_user')

        if (not tagged_phone_number and not tagged_user) or (tagged_phone_number and tagged_user):
            raise serializers.ValidationError(
                {"detail": "exactly one of tagged_user and tagged_phone_number is required"})

        return data

    def create(self, validated_data):
        tagged_phone_number = validated_data.get('tagged_phone_number')
        tagged_user = validated_data.get('tagged_user')
        tagging_user = validated_data.get('tagging_user')
        comment = validated_data.get('comment')

        matching_tagged_user = (
            tagged_user and
            Tag.objects.filter(
                comment_id=comment,
                tagging_user_id=tagging_user,
                tagged_user_id=tagged_user)
        )
        matching_tagged_phone_number = (
            tagged_phone_number and
            Tag.objects.filter(
                comment_id=comment,
                tagging_user_id=tagging_user,
                tagged_phone_number=tagged_phone_number)
        )

        if matching_tagged_user:
            raise serializers.ValidationError(
                {"detail": "commment, tagged_user, and tagging_user must make a unique set."})
        
        if matching_tagged_phone_number:
            raise serializers.ValidationError(
                {"detail": "comment, tagged_user, and tagged_phone_number must make a unique set."})
        
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            raise serializers.ValidationError({"detail": str(e)})

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
    votecount = serializers.SerializerMethodField()
    flagcount = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'body', 'timestamp', 
        'post', 'author', 'read_only_author',
        'votecount', 'flagcount', 'tags')

    def get_read_only_author(self, obj):
        return ReadOnlyUserSerializer(obj.author).data
    
    def get_tags(self, obj):
        tags = []
        try: tags = obj.tags.all()
        except: tags = Tag.objects.filter(comment_id=obj.id)
        return [TagSerializer(tag).data for tag in tags]
    
    def get_votecount(self, obj):
        try: return obj.votecount
        except: return obj.calculate_votecount()
    
    def get_flagcount(self, obj):
        try: return obj.flagcount
        except: return obj.calculate_flagcount()
    
    def validate_body(self, body):
        [is_offensive] = predict([body])
        if is_offensive:
            raise serializers.ValidationError("Avoid offensive language.")
        return body

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