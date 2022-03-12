from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def _str_(self):
        return self.username

class Post(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    title = models.CharField(max_length=40)
    text = models.CharField(max_length=1000)
    location = models.CharField(max_length=20, default="USC")
    timestamp = models.FloatField(default=0)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def _str_(self):
        return self.title
    
    def calculate_trendscore(self):
        votes = Vote.objects.filter(post_id=self.pk)
        net_rating = sum(vote.rating for vote in votes)
        return net_rating

class Vote(models.Model):
    voter = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField(default=0)
    rating = models.IntegerField(default=5)

    class Meta:
        unique_together = ('voter', 'post',)

    def _str_(self):
        return self.voter.pk

class Flag(models.Model):
    flagger = models.ForeignKey(Profile, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    timestamp = models.FloatField()
    rating = models.IntegerField()

    class Meta:
        unique_together = ('flagger', 'post',)

    def _str_(self):
        return self.flagger.pk

class Comment(models.Model):
    text = models.CharField(max_length=500)
    timestamp = models.FloatField(default=0)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, default="anonymous")

    def _str_(self):
        return self.text

class Message(models.Model):
    text = models.CharField(max_length=1000)
    timestamp = models.FloatField(default=0)
    from_user = models.ForeignKey(Profile, related_name='from_user', on_delete=models.CASCADE, null=True)
    to_user = models.ForeignKey(Profile, related_name='to_user', on_delete=models.CASCADE, null=True)

    def _str_(self):
        return self.text
