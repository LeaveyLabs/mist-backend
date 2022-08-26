from django.db.models import Count
from rest_framework import viewsets
from mist.generics import is_impermissible_comment
from mist.permissions import CommentPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import CommentSerializer

from ..models import Comment

class CommentView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, CommentPermission)
    serializer_class = CommentSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = self.filter_serialized_comments(response.data)
        return response
    
    def filter_serialized_comments(self, serialized_comments):
        filtered_comments = []
        for serialized_comment in serialized_comments:
            if not is_impermissible_comment(serialized_comment):
                filtered_comments.append(serialized_comment)
        return filtered_comments
    
    def get_queryset(self):
        """
        Returns comments matching the post.
        """
        post = self.request.query_params.get('post')
        queryset = None
        if post: queryset = Comment.objects.filter(post=post)
        else: queryset = Comment.objects.all()
        queryset = queryset.annotate(votecount=Count('commentvote'))
        queryset = queryset.annotate(flagcount=Count('commentflag'))
        queryset = queryset.prefetch_related('tags')
        queryset = queryset.order_by('timestamp')
        return queryset