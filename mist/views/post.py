from decimal import Decimal
from django.db.models.expressions import RawSQL
from rest_framework import viewsets, generics
from mist.permissions import PostPermission
from rest_framework.permissions import IsAuthenticated

from users.generics import get_user_from_request

from ..serializers import PostSerializer
from ..models import Favorite, Feature, FriendRequest, MatchRequest, Post

class PostView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, PostPermission,)
    serializer_class = PostSerializer

    # Max distance around post is 5 kilometer
    MAX_DISTANCE = Decimal(5)

    def get_locations_nearby_coords(self, latitude, longitude, max_distance=MAX_DISTANCE):
        """
        Return objects sorted by distance to specified coordinates
        which distance is less than max_distance given in kilometers
        """
        # Great circle distance formula
        gcd_formula = "6371 * acos(least(greatest(\
        cos(radians(%s)) * cos(radians(latitude)) \
        * cos(radians(longitude) - radians(%s)) + \
        sin(radians(%s)) * sin(radians(latitude)) \
        , -1), 1))"
        distance_raw_sql = RawSQL(
            gcd_formula,
            (latitude, longitude, latitude)
        )
        # make sure the latitude + longtitude exists
        # make sure the distance is under the max
        qs = Post.objects.all()\
        .filter(latitude__isnull=False)\
        .filter(longitude__isnull=False)\
        .annotate(distance=distance_raw_sql)\
        .order_by('distance')
        # distance must be less than max distance
        qs = qs.filter(distance__lt=max_distance)
        return qs

    def get_queryset(self):
        """
        Filter by text, location, and date. 
        If a parameter does not exist, then skip it. 
        Sort the result by vote ratings. 
        """
        # parameters
        ids = self.request.query_params.getlist('ids')
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = self.request.query_params.get('radius')
        words = self.request.query_params.getlist('words')
        start_timestamp = self.request.query_params.get('start_timestamp')
        end_timestamp = self.request.query_params.get('end_timestamp')
        location_description = self.request.query_params.get('location_description')
        author = self.request.query_params.get('author')
        # filter
        queryset = Post.objects.all()
        if latitude and longitude:
            queryset = self.get_locations_nearby_coords(
                latitude, longitude, radius or self.MAX_DISTANCE)
        if ids:
            queryset = queryset.filter(pk__in=ids)
        if words:
            for word in words:
                word_in_title = Post.objects.filter(title__icontains=word)
                word_in_body = Post.objects.filter(body__icontains=word)
                word_postset = (word_in_title | word_in_body).distinct()
                queryset = queryset.intersection(word_postset)
        if start_timestamp and end_timestamp:
            queryset = queryset.filter(
                timestamp__gte=start_timestamp,
                timestamp__lte=end_timestamp)
        if location_description:
            loc_set = queryset.filter(location_description__isnull=False)
            queryset = loc_set.filter(
                location_description__icontains=location_description)
        if author:
            queryset = queryset.filter(author=author)
        # order
        return queryset


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