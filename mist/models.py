from decimal import Decimal
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
import uuid
import string

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to='profiles', null=True)

    def _str_(self):
        return self.username

class Account(models.Model):
    phone_number = PhoneNumberField(null=True)

class UserRegistration(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    code_time = models.FloatField()
    validated = models.BooleanField(default=False)
    validation_time = models.FloatField(null=True)

class Post(models.Model):
    # Default coordinates are at USC
    USC_LATITUDE = Decimal(34.0224)
    USC_LONGITUDE = Decimal(118.2851)

    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=40)
    text = models.CharField(max_length=1000)
    location_description = models.CharField(max_length=40, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    timestamp = models.FloatField(default=0)
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
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=0)
    rating = models.IntegerField(default=5)

    class Meta:
        unique_together = ('voter', 'post',)

    def _str_(self):
        return self.voter.pk

class Flag(models.Model):
    flagger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField()
    rating = models.IntegerField()

    class Meta:
        unique_together = ('flagger', 'post',)

    def _str_(self):
        return self.flagger.pk

class Comment(models.Model):
    uuid = models.CharField(max_length=36, default=uuid.uuid4, unique=True)
    text = models.CharField(max_length=500)
    timestamp = models.FloatField(default=0)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def _str_(self):
        return self.text

class Message(models.Model):
    text = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=0)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='from_user', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='to_user', on_delete=models.CASCADE)

    def _str_(self):
        return self.text
