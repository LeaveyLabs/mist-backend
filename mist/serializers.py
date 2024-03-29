from psycopg2 import IntegrityError
# from profanity_check import predict
from rest_framework import serializers
from users.generics import get_current_time

from users.serializers import ReadOnlyUserSerializer
from .models import AccessCode, Block, CommentFlag, CommentVote, Favorite, Feature, Mistbox, PostFlag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, PostVote, View, Word

class WordSerializer(serializers.ModelSerializer):
    occurrences = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ('id', 'text', 'occurrences')
    
    def get_occurrences(self, obj):
        if obj.occurrences != None: return obj.occurrences
        return obj.calculate_occurrences()

class PostSerializer(serializers.ModelSerializer):
    votecount = serializers.SerializerMethodField()
    commentcount = serializers.SerializerMethodField()
    flagcount = serializers.SerializerMethodField()
    emoji_dict = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 
        'latitude', 'longitude', 'location_description',
        'timestamp', 'author', 'creation_time',
        'emoji_dict', 'commentcount', 'flagcount', 'votecount', 'collectible_type',
        'is_matched')
        read_only_fields = ('is_matched', )
    
    def get_flagcount(self, obj):
        try: obj.flags
        except: obj.flags = PostFlag.objects.filter(post_id=self.pk)
        return sum([flag.rating for flag in obj.flags.all()])
    
    def get_commentcount(self, obj):
        try: obj.comments
        except: obj.comments = Comment.objects.filter(post=self.pk)
        return obj.comments.count()

    def get_votecount(self, obj):
        try: obj.votes
        except: obj.votes = PostVote.objects.filter(post_id=obj.id)
        return sum([vote.rating for vote in obj.votes.all()])

    def get_trendscore(self, obj):
        try: obj.votes
        except: obj.votes = PostVote.objects.filter(post_id=obj.id)
        return sum([vote.rating*(vote.timestamp/get_current_time()) 
            for vote in obj.votes.all()])

    def get_emoji_dict(self, obj):
        try: votes = obj.votes
        except: votes = PostVote.objects.filter(post_id=obj.id)
        return self.convert_votes_to_emoji_dict(votes.all())

    def validate_body(self, body):
        # [is_offensive] = predict([body])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language.")
        return body

    def convert_votes_to_emoji_dict(self, votes):
        emoji_tuple = {}
        for vote in votes:
            if vote.emoji not in emoji_tuple:
                emoji_tuple[vote.emoji] = 0
            emoji_tuple[vote.emoji] += vote.rating
        return emoji_tuple

class PostVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVote
        fields = ('id', 'voter', 'post', 'timestamp', 'rating', 'emoji',)
    
class PostFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostFlag
        fields = ('id', 'flagger', 'post', 'timestamp', 'rating')

class TagSerializer(serializers.ModelSerializer):
    post = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ('id', 'comment', 'tagged_name', 'tagged_phone_number',
        'tagged_user', 'tagging_user', 'timestamp', 'post')
        extra_kwargs = {
            'tagged_phone_number': {'required': False},
            'tagged_user': {'required': False},
        }

    def get_post(self, obj):
        return PostSerializer(obj.comment.post).data
    
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
        try: tags = obj.tags
        except: tags = Tag.objects.filter(comment_id=obj.id)
        return [TagSerializer(tag).data for tag in tags.all()]

    def get_flagcount(self, obj):
        try: obj.flags
        except: obj.flags = CommentFlag.objects.filter(comment_id=self.pk)
        return sum([flag.rating for flag in obj.flags.all()])

    def get_votecount(self, obj):
        try: obj.votes
        except: obj.votes = CommentVote.objects.filter(comment_id=obj.id)
        return sum([vote.rating for vote in obj.votes.all()])
    
    def validate_body(self, body):
        # [is_offensive] = predict([body])
        # if is_offensive:
        #     raise serializers.ValidationError("Avoid offensive language.")
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

class MistboxSerializer(serializers.ModelSerializer):
    posts = serializers.SerializerMethodField()

    class Meta:
        model = Mistbox
        fields = ('user', 'keywords', 'creation_time', 'posts', 'opens_used_today')
        read_only_fields = ('user', 'creation_time', 'posts', 'opens_used_today')

    def validate_keywords(self, keywords):
        return [keyword.lower() for keyword in keywords]
    
    def get_posts(self, obj):
        from mist.views.post import Order
        try: obj.posts
        except: obj.posts = Post.objects.none()
        sorted_posts = sorted(obj.posts.all(), key=Order.recent, reverse=True)
        return [PostSerializer(post).data for post in sorted_posts]

class AccessCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessCode
        fields = ('code_string', 'claimed_user')

class AccessCodeClaimSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate_code(self, code):
        access_codes = AccessCode.objects.filter(code_string=code)
        if not access_codes.exists():
            raise serializers.ValidationError("Code does not exist")
        access_code = access_codes[0]
        if access_code.claimed_user:
            raise serializers.ValidationError("Already claimed")
        return code

class ViewPostSerializer(serializers.Serializer):
    posts = serializers.ListField(
        child = serializers.IntegerField()
    )