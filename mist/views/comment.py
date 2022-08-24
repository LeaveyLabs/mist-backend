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
        response.data = self.filter_and_order_serialized_comments(response.data)
        return response
    
    def filter_and_order_serialized_comments(self, serialized_comments):
        filtered_comments = []
        for serialized_comment in serialized_comments:
            if not is_impermissible_comment(serialized_comment):
                filtered_comments.append(serialized_comment)
        timestamp = lambda comment: comment.get('timestamp')
        ordered_comments = sorted(filtered_comments, key=timestamp)
        return ordered_comments
    
    def get_queryset(self):
        """
        Returns comments matching the post.
        """
        post = self.request.query_params.get('post')
        if post != None:
            return Comment.objects.filter(post=post)
        else:
            return Comment.objects.all()