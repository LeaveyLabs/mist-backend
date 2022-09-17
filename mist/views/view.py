from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from mist.serializers import ViewPostSerializer
from mist.models import Post, View
from users.generics import get_user_from_request

class ViewPost(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ViewPostSerializer

    def post(self, request, *args, **kwargs):
        post_views = ViewPostSerializer(data=request.data)
        post_views.is_valid(raise_exception=True)

        user = get_user_from_request(request)
        post_ids = post_views.data.get('posts')
        posts = Post.objects.filter(id__in=post_ids).all()
        for post in posts:
            View.objects.create(post=post, user=user)
        
        return Response(
            {
                "status": "success",
                "data": post_views.data
            }, 
            status.HTTP_201_CREATED)