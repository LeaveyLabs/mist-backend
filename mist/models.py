from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.forms import ValidationError
from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import string

def get_current_time():
    return datetime.now().timestamp()

# Post Interactions
class Post(models.Model):
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=40)
    body = models.CharField(max_length=1000)
    location_description = models.CharField(max_length=40, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    timestamp = models.FloatField(default=get_current_time)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.title
    
    def calculate_votecount(self):
        return PostVote.objects.filter(post_id=self.pk).count()
    
    def calculate_averagerating(self):
        votes = PostVote.objects.filter(post_id=self.pk)
        if len(votes) == 0: return 0
        return sum(vote.rating for vote in votes)/float(len(votes))
    
    def calculate_commentcount(self):
        return Comment.objects.filter(post=self.pk).count()
    
    def calculate_flagcount(self):
        return PostFlag.objects.filter(post=self.pk).count()
    
    def save(self, *args, **kwargs):
        # check if the post is new
        is_new = (len(Post.objects.filter(id=self.id)) == 0)
        # save original post
        super(Post, self).save(*args, **kwargs)
        # generate word
        if is_new:
            # gather all words in the post
            words_in_text = self.body.translate(
                str.maketrans('', '', string.punctuation)
                ).split()
            words_in_title = self.title.translate(
                str.maketrans('', '', string.punctuation)
                ).split()
            words_in_post = words_in_text + words_in_title
            # for each word ...
            for word in words_in_post:
                # ... if it doesn't exist create one
                matching_word = Word.objects.filter(text__iexact=word.lower()).first()
                if not matching_word:
                    matching_word = Word.objects.create(text=word.lower())

class Word(models.Model):
    text = models.CharField(max_length=100)
    posts = models.ManyToManyField(Post)
    
    def calculate_occurrences(self, wrapper_words=[]):
        word_in_title = Post.objects.filter(title__icontains=self.text)
        word_in_body = Post.objects.filter(body__icontains=self.text)
        postset = (word_in_title | word_in_body).distinct()
        for wrapper_word in wrapper_words:
            wrapper_in_title = Post.objects.filter(title__icontains=wrapper_word)
            wrapper_in_body = Post.objects.filter(body__icontains=wrapper_word)
            wrapper_postset = (wrapper_in_title | wrapper_in_body).distinct()
            postset = postset.intersection(wrapper_postset)
        return postset.count()

class PostVote(models.Model):
    MIN_RATING = 0
    MAX_RATING = 10
    AVG_RATING = (MIN_RATING+MAX_RATING)//2
    DEFAULT_EMOJI = "👍"

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)
    rating = models.IntegerField(default=AVG_RATING)
    emoji = models.CharField(max_length=5, default=DEFAULT_EMOJI)

    class Meta:
        unique_together = ('voter', 'post',)

    def _str_(self):
        return self.voter.pk

class PostFlag(models.Model):
    MIN_RATING = 0
    MAX_RATING = 10
    AVG_RATING = (MIN_RATING+MAX_RATING)//2

    flagger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)
    rating = models.IntegerField(default=AVG_RATING)

    class Meta:
        unique_together = ('flagger', 'post',)

    def _str_(self):
        return self.flagger.pk

class Comment(models.Model):
    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    body = models.CharField(max_length=500)
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.text
    
    def calculate_votecount(self):
        return CommentVote.objects.filter(comment_id=self.pk).count()
    
    def calculate_flagcount(self):
        return CommentFlag.objects.filter(comment_id=self.pk).count()

class Tag(models.Model):
    DEFAULT_NAME = "anonymous"

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
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
    MIN_RATING = 0
    MAX_RATING = 10
    AVG_RATING = (MIN_RATING+MAX_RATING)//2

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)
    rating = models.IntegerField(default=AVG_RATING)

    class Meta:
        unique_together = ('voter', 'comment',)

    def _str_(self):
        return self.voter.pk

class CommentFlag(models.Model):
    MIN_RATING = 0
    MAX_RATING = 10
    AVG_RATING = (MIN_RATING+MAX_RATING)//2

    flagger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)
    rating = models.IntegerField(default=AVG_RATING)

    class Meta:
        unique_together = ('flagger', 'comment',)

    def _str_(self):
        return self.flagger.pk

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
    blocking_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking_user', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_user', on_delete=models.CASCADE)
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

class Message(models.Model):
    body = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=get_current_time)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='receiver', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return self.text