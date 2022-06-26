from decimal import Decimal
from django.db.models.expressions import RawSQL
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from mist.permissions import BlockPermission, CommentPermission, FavoritePermission, FlagPermission, FriendRequestPermission, MatchRequestPermission, MessagePermission, PostPermission, TagPermission, VotePermission
from rest_framework.permissions import IsAuthenticated

from users.models import User

from .serializers import (
    BlockSerializer,
    FavoriteSerializer,
    FeatureSerializer,
    FlagSerializer,
    FriendRequestSerializer,
    MatchRequestSerializer,
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    TagSerializer,
    VoteSerializer,
    WordSerializer,
)
from .models import (
    Block,
    Favorite,
    Feature,
    Flag,
    FriendRequest,
    MatchRequest,
    Post, 
    Comment,
    Message,
    Tag,
    Vote,
    Word,
)

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

class WordView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = WordSerializer

    def get_queryset(self):
        # parameters
        search_word = self.request.query_params.get('search_word')
        wrapper_words = self.request.query_params.getlist('wrapper_words')
        # filter
        if search_word == None: 
            return Word.objects.none()
        
        search_word_objs = Word.objects.filter(text__icontains=search_word)
        for search_word_obj in search_word_objs:
            search_word_obj.occurrences = search_word_obj.calculate_occurrences(wrapper_words)
        
        return search_word_objs

class CommentView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, CommentPermission)
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """
        Returns comments matching the post.
        """
        post = self.request.query_params.get('post')
        if post != None:
            return Comment.objects.filter(post=post)
        else:
            return Comment.objects.all()

class VoteView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, VotePermission)
    serializer_class = VoteSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()
            
    def get_object_by_query_params(self):
        voter = self.request.query_params.get("voter")
        post = self.request.query_params.get("post")
        matching_vote = get_object_or_404(
            Vote.objects.all(), 
            voter=voter,
            post=post)
        self.check_object_permissions(self.request, matching_vote)
        return matching_vote

    def get_queryset(self):
        """
        If parameters are missing, return all votes.
        Otherwise, return with user and post.
        """
        # parameters
        voter = self.request.query_params.get("voter")
        post = self.request.query_params.get("post")
        # filters
        queryset = Vote.objects.all()
        if voter:
            matching_users = User.objects.filter(pk=voter)
            if not matching_users: return Vote.objects.none()
            queryset = queryset.filter(voter=matching_users[0])
        if post:
            queryset = queryset.filter(post=post)
        return queryset

class FlagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FlagPermission)
    serializer_class = FlagSerializer

    def get_queryset(self):
        flagger = self.request.query_params.get("flagger")
        post = self.request.query_params.get("post")
        queryset = Flag.objects.all()
        if flagger:
            queryset = queryset.filter(flagger=flagger)
        if post:
            queryset = queryset.filter(post=post)
        return queryset

class TagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, TagPermission)
    serializer_class = TagSerializer

    def get_queryset(self):
        tagged_user = self.request.query_params.get("tagged_user")
        tagging_user = self.request.query_params.get("tagging_user")
        post = self.request.query_params.get("post")
        queryset = Tag.objects.all()
        if tagged_user:
            queryset = queryset.filter(tagged_user=tagged_user)
        if tagging_user:
            queryset = queryset.filter(tagging_user=tagging_user)
        if post:
            queryset = queryset.filter(post=post)
        return queryset

class BlockView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, BlockPermission)
    serializer_class = BlockSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()

    def get_object_by_query_params(self):
        blocked_user = self.request.query_params.get("blocked_user")
        blocking_user = self.request.query_params.get("blocking_user")
        matching_block = get_object_or_404(
            Block.objects.all(), 
            blocked_user=blocked_user,
            blocking_user=blocking_user)
        self.check_object_permissions(self.request, matching_block)
        return matching_block

    def get_queryset(self):
        blocked_user = self.request.query_params.get("blocked_user")
        blocking_user = self.request.query_params.get("blocking_user")
        queryset = Block.objects.all()
        if blocked_user:
            queryset = queryset.filter(blocked_user=blocked_user)
        if blocking_user:
            queryset = queryset.filter(blocking_user=blocking_user)
        return queryset

class MessageView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, MessagePermission)
    serializer_class = MessageSerializer

    def get_queryset(self):
        sender = self.request.query_params.get("sender")
        receiver = self.request.query_params.get("receiver")
        queryset = Message.objects.all()
        if receiver:
            queryset = queryset.filter(receiver=receiver)
        if sender:
            queryset = queryset.filter(sender=sender)
        return queryset

class FriendRequestView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FriendRequestPermission)
    serializer_class = FriendRequestSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()
    
    def get_object_by_query_params(self):
        friend_requesting_user = self.request.query_params.get("friend_requesting_user")
        friend_requested_user = self.request.query_params.get("friend_requested_user")
        matching_friend_request = get_object_or_404(
            FriendRequest.objects.all(), 
            friend_requesting_user=friend_requesting_user,
            friend_requested_user=friend_requested_user)
        self.check_object_permissions(self.request, matching_friend_request)
        return matching_friend_request

    def get_queryset(self):
        friend_requesting_user = self.request.query_params.get("friend_requesting_user")
        friend_requested_user = self.request.query_params.get("friend_requested_user")
        queryset = FriendRequest.objects.all()
        if friend_requesting_user:
            queryset = queryset.filter(friend_requesting_user=friend_requesting_user)
        if friend_requested_user:
            queryset = queryset.filter(friend_requested_user=friend_requested_user)
        return queryset

class MatchRequestView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, MatchRequestPermission)
    serializer_class = MatchRequestSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()
    
    def get_object_by_query_params(self):
        match_requesting_user = self.request.query_params.get("match_requesting_user")
        match_requested_user = self.request.query_params.get("match_requested_user")
        matching_match_request = get_object_or_404(
            MatchRequest.objects.all(), 
            match_requesting_user=match_requesting_user,
            match_requested_user=match_requested_user)
        self.check_object_permissions(self.request, matching_match_request)
        return matching_match_request

    def get_queryset(self):
        match_requesting_user = self.request.query_params.get("match_requesting_user")
        match_requested_user = self.request.query_params.get("match_requested_user")
        queryset = MatchRequest.objects.all()
        if match_requesting_user:
            queryset = queryset.filter(match_requesting_user=match_requesting_user)
        if match_requested_user:
            queryset = queryset.filter(match_requested_user=match_requested_user)
        return queryset
    
class FavoriteView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FavoritePermission)
    serializer_class = FavoriteSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg in self.kwargs:
            return super().get_object()
        else:
            return self.get_object_by_query_params()
    
    def get_object_by_query_params(self):
        favoriting_user = self.request.query_params.get("favoriting_user")
        post = self.request.query_params.get("post")
        matching_block = get_object_or_404(
            Favorite.objects.all(), 
            favoriting_user=favoriting_user,
            post=post)
        self.check_object_permissions(self.request, matching_block)
        return matching_block
    
    def get_queryset(self):
        favoriting_user = self.request.query_params.get("favoriting_user")
        queryset = Favorite.objects.all()
        if favoriting_user:
            queryset = queryset.filter(favoriting_user=favoriting_user)
        return queryset

class FeatureView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FeatureSerializer

    def get_queryset(self):
        post = self.request.query_params.get("post")
        timestamp = self.request.query_params.get("timestamp")
        queryset = Feature.objects.all()
        if post:
            queryset = queryset.filter(post=post)
        if timestamp:
            queryset = queryset.filter(timestamp=timestamp)
        return queryset

