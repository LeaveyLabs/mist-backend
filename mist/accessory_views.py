from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from mist.models import Favorite, Feature, FriendRequest, MatchRequest, Post
from mist.serializers import PostSerializer
from users.generics import get_user_from_request
from users.models import User
from users.serializers import ReadOnlyUserSerializer

# Custom User Views
class MatchView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReadOnlyUserSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        sent_match_requests = MatchRequest.objects.filter(
            match_requesting_user=user,
        )
        requested_user_pks = sent_match_requests.values_list('match_requested_user_id')
        matched_match_requests = MatchRequest.objects.filter(
            match_requesting_user__in=requested_user_pks,
            match_requested_user=user,
        )
        matched_user_pks = matched_match_requests.values_list('match_requesting_user')
        matched_users = User.objects.filter(pk__in=matched_user_pks)
        return matched_users

class FriendshipView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReadOnlyUserSerializer
    
    def get_queryset(self):
        user = get_user_from_request(self.request)
        sent_friend_requests = FriendRequest.objects.filter(
            friend_requesting_user=user,
        )
        requested_user_pks = sent_friend_requests.values_list('friend_requested_user_id')
        matched_friend_requests = FriendRequest.objects.filter(
            friend_requesting_user__in=requested_user_pks,
            friend_requested_user=user,
        )
        friend_pks = matched_friend_requests.values_list('friend_requesting_user')
        friends = User.objects.filter(pk__in=friend_pks)
        return friends

# Custom Post Views
class MatchedPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        match_requests = MatchRequest.objects.all()
        sent_request_pks = match_requests.values_list('match_requested_user_id', 
                                                    'match_requesting_user_id')
        matched_requests = MatchRequest.objects.none()
        for requested_user_pk, requesting_user_pk in sent_request_pks:
            received_requests = MatchRequest.objects.filter(
                                match_requesting_user=requested_user_pk,
                                match_requested_user=requesting_user_pk)
            matched_requests = matched_requests | received_requests
        matched_post_pks = matched_requests.values_list('post')
        matched_posts = Post.objects.filter(pk__in=matched_post_pks)
        return matched_posts

class FeaturedPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        featured_post_pks = Feature.objects.values_list('post')
        featured_posts = Post.objects.filter(pk__in=featured_post_pks)
        return featured_posts

class FriendPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        sent_friend_requests = FriendRequest.objects.filter(
            friend_requesting_user=user,
        )
        requested_user_pks = sent_friend_requests.values_list('friend_requested_user_id')
        matched_friend_requests = FriendRequest.objects.filter(
            friend_requesting_user__in=requested_user_pks,
            friend_requested_user=user,
        )
        friend_pks = matched_friend_requests.values_list('friend_requesting_user')
        return Post.objects.filter(author_id__in=friend_pks)

class FavoritedPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        favorited_post_pks = Favorite.objects.filter(favoriting_user=user).values_list('post')
        return Post.objects.filter(pk__in=favorited_post_pks)

class SubmittedPostsView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        return Post.objects.filter(author=user)