from django.contrib import admin
from .models import Block, Favorite, Feature, PostFlag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, PostVote, Word

# Register your models here.
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(PostVote)
admin.site.register(PostFlag)
admin.site.register(Tag)
admin.site.register(Block)
admin.site.register(Word)
admin.site.register(Feature)
admin.site.register(MatchRequest)
admin.site.register(FriendRequest)
admin.site.register(Favorite)