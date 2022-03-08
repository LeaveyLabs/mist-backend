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
    title = models.CharField(max_length=40)
    text = models.CharField(max_length=1000)
    location = models.CharField(max_length=20, default="USC")
    date = models.DateField()
    votes = models.ManyToManyField(Profile, related_name="votes", blank=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def _str_(self):
        return self.title
    
class Comment(models.Model):
    text = models.CharField(max_length=500)
    date = models.DateField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, default="anonymous")

    def _str_(self):
        return self.text

class Message(models.Model):
    text = models.CharField(max_length=1000)
    date = models.DateField()
    from_user = models.ForeignKey(Profile, related_name='from_user', on_delete=models.CASCADE, null=True)
    to_user = models.ForeignKey(Profile, related_name='to_user', on_delete=models.CASCADE, null=True)

    def _str_(self):
        return self.text
