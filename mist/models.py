from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.db import models
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
        return Vote.objects.filter(post_id=self.pk).count()
    
    def calculate_averagerating(self):
        votes = Vote.objects.filter(post_id=self.pk)
        if len(votes) == 0: return 0
        return sum(vote.rating for vote in votes)/float(len(votes))
    
    def calculate_commentcount(self):
        return Comment.objects.filter(post=self.pk).count()
    
    def calculate_flagcount(self):
        return Flag.objects.filter(post=self.pk).count()
    
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

class Vote(models.Model):
    MIN_RATING = 0
    MAX_RATING = 10
    AVG_RATING = (MIN_RATING+MAX_RATING)//2

    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time)
    rating = models.IntegerField(default=AVG_RATING)

    class Meta:
        unique_together = ('voter', 'post',)

    def _str_(self):
        return self.voter.pk

class Flag(models.Model):
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

class Tag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    tagged_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tagged_user', on_delete=models.CASCADE)
    tagging_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='tagging_user', on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time, null=True)

    class Meta:
        unique_together = ('tagged_user', 'tagging_user',)

class Comment(models.Model):
    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    body = models.CharField(max_length=500)
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.text

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
    post = models.ForeignKey(Post, on_delete=models.SET_NULL)
    timestamp = models.FloatField(default=get_current_time, null=True)
        
    class Meta:
        unique_together = ('match_requesting_user', 'match_requested_user', 'post')

class Message(models.Model):
    body = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=get_current_time)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='receiver', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)

    def _str_(self):
        return self.text