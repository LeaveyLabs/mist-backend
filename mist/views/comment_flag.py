from rest_framework import viewsets
from mist.generics import is_beyond_impermissible_comment_limit
from mist.permissions import FlagPermission
from rest_framework.permissions import IsAuthenticated

from users.models import Ban

from ..serializers import CommentFlagSerializer, CommentSerializer
from ..models import Comment, CommentFlag

class CommentFlagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FlagPermission)
    serializer_class = CommentFlagSerializer

    def get_queryset(self):
        flagger = self.request.query_params.get("flagger")
        comment = self.request.query_params.get("comment")
        queryset = CommentFlag.objects.all()
        if flagger:
            queryset = queryset.filter(flagger=flagger)
        if comment:
            queryset = queryset.filter(comment=comment)
        return queryset.prefetch_related('flagger', 'comment')

    def create(self, request, *args, **kwargs):
        comment_flag_response = super().create(request, *args, **kwargs)
        comment_id = comment_flag_response.data.get("comment")
        comment_author = Comment.objects.get(id=comment_id).author
        comments_by_author = Comment.objects.filter(
            author=comment_author).\
            prefetch_related("votes", "flags", "tags").\
            select_related('author').\
            prefetch_related("author__badges")
        serialized_comments_by_author = [
            CommentSerializer(comment).data for comment in comments_by_author
        ]
        if is_beyond_impermissible_comment_limit(serialized_comments_by_author):
            Ban.objects.get_or_create(phone_number=comment_author.phone_number)
        return comment_flag_response