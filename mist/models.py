from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.db import models
import uuid
import string

def get_current_time():
    return datetime.now().timestamp()

class Post(models.Model):
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=40)
    text = models.CharField(max_length=1000)
    location_description = models.CharField(max_length=40, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    timestamp = models.FloatField(default=get_current_time)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.title
    
    def calculate_averagerating(self):
        votes = Vote.objects.filter(post_id=self.pk)
        if len(votes) == 0: return 0
        return sum(vote.rating for vote in votes)/float(len(votes))
    
    def calculate_commentcount(self):
        return len(Comment.objects.filter(post=self.pk))
    
    def save(self, *args, **kwargs):
        # check if the post is new
        is_new = (len(Post.objects.filter(id=self.id)) == 0)
        # save original post
        super(Post, self).save(*args, **kwargs)
        # generate word
        if is_new:
            # gather all words in the post
            words_in_text = self.text.translate(
                str.maketrans('', '', string.punctuation)
                ).split()
            words_in_title = self.title.translate(
                str.maketrans('', '', string.punctuation)
                ).split()
            words_in_post = words_in_text + words_in_title
            # for each word ...
            for word in words_in_post:
                # ... if it doesn't exist create one
                matching_words = Word.objects.filter(text=word)
                if len(matching_words) == 0:
                    word_obj = Word.objects.create(text=word)
                    word_obj.posts.add(self)
                # ... increment occurrences
                else:
                    matching_words[0].posts.add(self)

class Word(models.Model):
    text = models.CharField(max_length=100)
    posts = models.ManyToManyField(Post)

    def calculate_occurrences(self):
        return self.posts.count()

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

class Block(models.Model):
    blocking_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking_user', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_user', on_delete=models.CASCADE)
    timestamp = models.FloatField(default=get_current_time, null=True)

    class Meta:
        unique_together = ('blocking_user', 'blocked_user',)

class Comment(models.Model):
    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    text = models.CharField(max_length=500)
    timestamp = models.FloatField(default=get_current_time)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.text

class Message(models.Model):
    text = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=get_current_time)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='from_user', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='to_user', on_delete=models.CASCADE)

    def _str_(self):
        return self.text

    
