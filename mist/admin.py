from django.contrib import admin
from .models import Profile, Post, Comment, Message, RegistrationRequest, ValidationRequest, Vote

# Register your models here.
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(Vote)
admin.site.register(RegistrationRequest)
admin.site.register(ValidationRequest)