from django.contrib import admin

from mist.serializers import PostSerializer

from .models import AccessCode, Block, CommentFlag, CommentVote, Favorite, Feature, Mistbox, PostFlag, FriendRequest, MatchRequest, Post, Comment, Message, Tag, PostVote, Word

# Admin models
class PostAdmin(admin.ModelAdmin):
    model = Post
    list_display = ("id", "title", "body", "author")

class CommentAdmin(admin.ModelAdmin):
    model = Comment
    list_display = ("id", "post_id", "post_title", "body", "author")

    def post_title(self, obj):
        return Post.objects.get(id=obj.post_id).title

class PostVoteAdmin(admin.ModelAdmin):
    model = PostVote
    list_display = ("id", "post_id", "post_title", "post_body", "voter")

    def post_title(self, obj):
        return Post.objects.get(id=obj.post_id).title
    
    def post_body(self, obj):
        return Post.objects.get(id=obj.post_id).body

class PostFlagAdmin(admin.ModelAdmin):
    model = PostFlag
    list_display = ("id", "post_id", "post_title", "post_body", "flagger")

    def post_title(self, obj):
        return Post.objects.get(id=obj.post_id).title
    
    def post_body(self, obj):
        return Post.objects.get(id=obj.post_id).body

class CommentVoteAdmin(admin.ModelAdmin):
    model = CommentVote
    list_display = ("id", "comment_id", "comment_body", "voter")
    
    def comment_body(self, obj):
        return Comment.objects.get(id=obj.comment_id).body

class CommentFlagAdmin(admin.ModelAdmin):
    model = CommentFlag
    list_display = ("id", "comment_id", "comment_body", "flagger")
    
    def comment_body(self, obj):
        return Comment.objects.get(id=obj.comment_id).body

class MistboxAdmin(admin.ModelAdmin):
    model = Mistbox
    list_display = ("id", "user", "post_list")

    def post_list(self, obj):
        return [PostSerializer(post).data.get('title') for post in obj.posts.all()]

class AccessCodeAdmin(admin.ModelAdmin):
    model = AccessCode
    list_display = ("code_string", "claimed_user")

# Register your models here.
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostVote, PostVoteAdmin)
admin.site.register(PostFlag, PostFlagAdmin)
admin.site.register(CommentVote, CommentVoteAdmin)
admin.site.register(CommentFlag, CommentFlagAdmin)
admin.site.register(Mistbox, MistboxAdmin)
admin.site.register(AccessCode, AccessCodeAdmin)
admin.site.register(Message)
admin.site.register(Tag)
admin.site.register(Block)
admin.site.register(Word)
admin.site.register(Feature)
admin.site.register(MatchRequest)
admin.site.register(FriendRequest)
admin.site.register(Favorite)
