from rest_framework import viewsets
from mist.generics import is_impermissible_comment
from mist.permissions import CommentPermission
from users.models import User
from push_notifications.models import APNSDevice
from rest_framework.permissions import IsAuthenticated

from ..serializers import CommentSerializer

from ..models import Comment, NotificationTypes, Post

class CommentView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, CommentPermission)
    serializer_class = CommentSerializer

    def create(self, request, *args, **kwargs):
        comment_response = super().create(request, *args, **kwargs)
        post_id = comment_response.data.get('post')
        commenter_id = comment_response.data.get('author')
        commenter = User.objects.get(id=commenter_id)
        post_author = Post.objects.get(id=post_id).author
        APNSDevice.objects.filter(user=post_author).send_message(
            f"{commenter.first_name} {commenter.last_name} commented on your mist",
            extra={
                "type": NotificationTypes.COMMENT,
                "data": comment_response.data
            }
        )
        return comment_response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # serialized_posts = response.data.get('results')
        # response.data['results'] = self.filter_serialized_comments(serialized_posts)
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
        return queryset.\
            prefetch_related("votes", "flags", "tags").\
            prefetch_related("post__votes").\
            prefetch_related("post__flags").\
            prefetch_related("post__comments").\
            select_related('author', 'post', 'post__author',).\
            prefetch_related("author__badges").\
            order_by('timestamp')