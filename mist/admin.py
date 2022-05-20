from django.contrib import admin
from .models import Block, Flag, Post, Comment, Message, Tag, Vote, Word

# Register your models here.
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(Vote)
admin.site.register(Flag)
admin.site.register(Tag)
admin.site.register(Block)
admin.site.register(Word)