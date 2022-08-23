from rest_framework import viewsets
import math
from mist.permissions import CommentPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import CommentSerializer

from ..models import Comment

def is_impermissible_comment(votecount, flagcount):
    LOWER_FLAG_BOUND = 2
    return flagcount > LOWER_FLAG_BOUND and flagcount > math.sqrt(votecount)

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
            flagcount = serialized_comment.get('flagcount')
            votecount = serialized_comment.get('votecount')
            if not is_impermissible_comment(votecount, flagcount):
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