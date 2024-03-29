from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q, Count
from django.forms import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import string
from users.generics import get_empty_keywords

from users.models import User

def get_current_time():
    return datetime.now().timestamp()

# Post Interactions
class Post(models.Model):
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    NUMBER_OF_TOTAL_COLLECTIBLES = 30

    BAD_WORDS = [
        'fuck', 
        'fuk', 
        'dick', 
        'sex',
        'bitch',
        'queef',
    ]

    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=40)
    body = models.CharField(max_length=1000)
    location_description = models.CharField(max_length=40, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.FloatField(default=get_current_time)
    creation_time = models.FloatField(default=get_current_time)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    collectible_type = models.PositiveIntegerField(null=True, blank=True)
    is_matched = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    def _str_(self):
        return self.title
    
    def calculate_votecount(self):
        return PostVote.objects.filter(post_id=self.pk).count()
    
    def calculate_commentcount(self):
        return Comment.objects.filter(post=self.pk).count()
    
    def calculate_flagcount(self):
        superusers = User.objects.filter(is_superuser=True)
        flags = PostFlag.objects.filter(post_id=self.pk)
        if flags.filter(flagger__in=superusers):
            return float('inf')
        return flags.count()
    
    def save(self, *args, **kwargs):
        from profanity_check import predict
        
        # check if the post is new
        is_new = (len(Post.objects.filter(id=self.id)) == 0)

        # ai profanity check
        if self.body and predict([self.body]):
            self.is_hidden = True
        if self.title and predict([self.title]):
            self.is_hidden = True
        if self.location_description and predict([self.location_description]):
            self.is_hidden = True
        
        # manual profanity check
        for word in self.BAD_WORDS:
            if self.body and word in self.body.lower():
                self.is_hidden = True
                break
            if self.title and word in self.title.lower():
                self.is_hidden = True
                break
            if self.location_description and word in self.location_description.lower():
                self.is_hidden = True
                break
        
        # save original post
        super(Post, self).save(*args, **kwargs)
        # generate word
        if is_new:
            # gather all words in the post
            words_in_text = []
            words_in_title = []
            words_in_loc = []

            if self.body:
                words_in_text = self.body.translate(
                    str.maketrans('', '', string.punctuation)
                    ).split()
            if self.title:
                words_in_title = self.title.translate(
                    str.maketrans('', '', string.punctuation)
                    ).split()
            if self.location_description:
                words_in_loc = self.location_description.translate(
                    str.maketrans('', '', string.punctuation)
                    ).split()
            
            words_in_post = words_in_text + words_in_title + words_in_loc
            mistboxes = Mistbox.objects.all().\
                exclude(user=self.author).\
                select_related('user').\
                prefetch_related('posts')
            # sent_user_ids = []
            # for each word ...            
            for word in words_in_post:
                lowercased_word = word.lower()
                # ... if it doesn't exist create one
                matching_word = Word.objects.filter(text__iexact=lowercased_word).first()
                if not matching_word:
                    matching_word = Word.objects.create(text=lowercased_word)
                
                for mistbox in mistboxes:
                    for keyword in mistbox.keywords:
                        if keyword in lowercased_word:
                            mistbox.posts.add(self)
                            mistbox.save()
                            # if mistbox.user.id not in sent_user_ids:
                            #     UserNotification.objects.create(
                            #         user_id=mistbox.user.id,
                            #         type=UserNotification.NotificationTypes.DAILY_MISTBOX,
                            #         message="you got a new mist in your mistbox 💌",
                            #     )
                            #     sent_user_ids.append(mistbox.user.id)

class Word(models.Model):
    text = models.CharField(max_length=100)
    posts = models.ManyToManyField(Post)
    
    def calculate_occurrences(self, wrapper_words=[]):
        query = (Q(title__icontains=self.text) | Q(body__icontains=self.text))
        for wrapper_word in wrapper_words:
            query &= (Q(title__icontains=wrapper_word) | Q(body__icontains=wrapper_word))
        postset = Post.objects.filter(query).distinct()
        return postset\
            .annotate(flagcount=Count('flags'))\
            .exclude(flagcount__gt=0, flagcount__isnull=False)\
            .count()

class PostVote(models.Model):
    DEFAULT_RATING = 1
    DEFAULT_EMOJI = "❤️"

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='postvotes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.FloatField(default=get_current_time)
    rating = models.FloatField(default=DEFAULT_RATING)
    emoji = models.CharField(max_length=5, default=DEFAULT_EMOJI)

    class Meta:
        unique_together = ('voter', 'post',)

    def _str_(self):
        return self.voter.pk

class PostFlag(models.Model):
    DEFAULT_RATING = 1
    VERY_LARGE_RATING = 1000

    flagger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='postflags')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='flags')
    timestamp = models.FloatField(default=get_current_time)
    rating = models.FloatField(default=DEFAULT_RATING)

    class Meta:
        unique_together = ('flagger', 'post',)

    def _str_(self):
        return self.flagger.pk

    def save(self, *args, **kwargs):
        if self.flagger.is_superuser: 
            self.rating = self.VERY_LARGE_RATING
        super().save(*args, **kwargs)

class Comment(models.Model):
    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    body = models.CharField(max_length=500)
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')

    def _str_(self):
        return self.text
    
    def calculate_votecount(self):
        return CommentVote.objects.filter(comment_id=self.pk).count()
    
    def calculate_flagcount(self):
        superusers = User.objects.filter(is_superuser=True)
        flags = CommentFlag.objects.filter(comment_id=self.pk)
        if flags.filter(flagger__in=superusers):
            return float('inf')
        return flags.count()

class Tag(models.Model):
    DEFAULT_NAME = "anonymous"

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='tags')
    tagged_name = models.CharField(max_length=50, default=DEFAULT_NAME)
    tagging_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tagging_user', on_delete=models.CASCADE)
    tagged_phone_number = PhoneNumberField(null=True)
    tagged_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tagged_user', on_delete=models.CASCADE, null=True)
    timestamp = models.FloatField(default=get_current_time, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['comment', 'tagged_user', 'tagging_user'], name='tagged_user_tagging_user'),
            models.UniqueConstraint(fields=['comment', 'tagged_phone_number', 'tagging_user'], name='tagged_phone_number_tagging_user'),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_tagged_phone_number_or_tagged_user",
                check=(
                    models.Q(tagged_user__isnull=True, tagged_phone_number__isnull=False)
                    | models.Q(tagged_user__isnull=False, tagged_phone_number__isnull=True)
                ),
            )
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('tagged_user') and not cleaned_data.get('tagged_phone_number'):  # This will check for None or Empty
            raise ValidationError({'detail': 'Even one of tagged_user or tagged_phone_number should have a value.'})

    # def save(self, *args, **kwargs):
    #     both_tagged_fields = self.tagged_user and self.tagged_phone_number
    #     no_tagged_fields = not self.tagged_user and not self.tagged_phone_number
    #     if both_tagged_fields or no_tagged_fields:
    #         raise serializers.ValidationError(
    #             {'detail': 'Exactly one of tagged_user or tagged_phone_number should have a value.'})
    #     super(Tag, self).save(*args, **kwargs)

class CommentVote(models.Model):
    DEFAULT_RATING = 1

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commentvotes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.FloatField(default=get_current_time)
    rating = models.FloatField(default=DEFAULT_RATING)

    class Meta:
        unique_together = ('voter', 'comment',)

    def _str_(self):
        return self.voter.pk

class CommentFlag(models.Model):
    DEFAULT_RATING = 1
    VERY_LARGE_RATING = 1000

    flagger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commentflags')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    timestamp = models.FloatField(default=get_current_time)
    rating = models.FloatField(default=DEFAULT_RATING)

    class Meta:
        unique_together = ('flagger', 'comment',)

    def _str_(self):
        return self.flagger.pk

    def save(self, *args, **kwargs):
        if self.flagger.is_superuser:
            self.rating = self.VERY_LARGE_RATING
        super().save(*args, **kwargs)

class Favorite(models.Model):
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    favoriting_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'favoriting_user',)

class Feature(models.Model):
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

# User Interactions
class Block(models.Model):
    blocking_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blockings', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocks', on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time, null=True)

    class Meta:
        unique_together = ('blocking_user', 'blocked_user',)

class FriendRequest(models.Model):
    friend_requesting_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requesting_user', on_delete=models.CASCADE)
    friend_requested_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requested_user', on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time, null=True)

    class Meta:
        unique_together = ('friend_requesting_user', 'friend_requested_user',)

class MatchRequest(models.Model):
    match_requesting_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='match_requesting_user', on_delete=models.CASCADE)
    match_requested_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='match_requested_user', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, null=True, on_delete=models.SET_NULL)
    timestamp = models.FloatField(default=get_current_time, null=True)
        
    class Meta:
        unique_together = ('match_requesting_user', 'match_requested_user')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        oppposite_requests = MatchRequest.objects.filter(
            match_requesting_user=self.match_requested_user,
            match_requested_user=self.match_requesting_user,
        )
        if oppposite_requests.exists():
            opposite_requests = Q(
                match_requesting_user=self.match_requested_user,
                match_requested_user=self.match_requesting_user)
            same_requests = Q(
                match_requesting_user=self.match_requesting_user,
                match_requested_user=self.match_requested_user)
            bidirectional_requests = MatchRequest.objects.filter(
                opposite_requests | same_requests).select_related('post')
            for request in bidirectional_requests:
                if request.post:
                    request.post.is_matched = True
                    request.post.save()


class Message(models.Model):
    body = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=get_current_time)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='receiver', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_hidden = models.BooleanField(default=False)

    def _str_(self):
        return self.text

class Mistbox(models.Model):
    NUMBER_OF_KEYWORDS = 10
    MAX_DAILY_SWIPES = 10

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='mistbox', on_delete=models.CASCADE)
    keywords = ArrayField(models.TextField(), size=NUMBER_OF_KEYWORDS, default=get_empty_keywords, blank=True)
    creation_time = models.FloatField(default=get_current_time)
    posts = models.ManyToManyField(Post, blank=True)
    opens_used_today = models.IntegerField(default=0)

class AccessCode(models.Model):
    code_string = models.CharField(max_length=6, unique=True)
    claimed_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='access_code', on_delete=models.CASCADE, null=True)

class Badge(models.Model):
    LOVE_MIST = 'LM'

    BADGE_OPTIONS = (
        (LOVE_MIST, 'LOVE, MIST'),
    )

    badge_type = models.CharField(max_length=2, choices=BADGE_OPTIONS,)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='badges', on_delete=models.CASCADE)

class View(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='views', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='views', on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)