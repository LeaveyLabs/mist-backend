from rest_framework import viewsets
from mist.generics import is_beyond_impermissible_post_limit
from mist.permissions import FlagPermission
from rest_framework.permissions import IsAuthenticated
from mist.views.post import is_impermissible_post

from users.models import Ban

from ..serializers import PostFlagSerializer, PostSerializer
from ..models import Post, PostFlag

class PostFlagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FlagPermission)
    serializer_class = PostFlagSerializer

    def get_queryset(self):
        flagger = self.request.query_params.get("flagger")
        post = self.request.query_params.get("post")
        queryset = PostFlag.objects.all()
        if flagger:
            queryset = queryset.filter(flagger=flagger)
        if post:
            queryset = queryset.filter(post=post)
        return queryset

    def create(self, request, *args, **kwargs):
        post_flag_response = super().create(request, *args, **kwargs)
        post_id = post_flag_response.data.get("post")
        post_author = Post.objects.get(id=post_id).author
        posts_by_author = Post.objects.filter(author=post_author)
        serialized_posts_by_author = [
            PostSerializer(post).data for post in posts_by_author
        ]
        if is_beyond_impermissible_post_limit(serialized_posts_by_author):
            Ban.objects.get_or_create(email=post_author.email)
        return post_flag_response