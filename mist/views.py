from decimal import Decimal
from django.db.models import Avg, Count
from django.db.models.expressions import RawSQL
from rest_framework import viewsets, generics
from users.models import User

from .serializers import (
    BlockSerializer,
    FlagSerializer,
    PostSerializer, 
    CommentSerializer,
    MessageSerializer,
    TagSerializer,
    VoteSerializer,
    WordSerializer,
)
from .models import (
    Block,
    Flag,
    Post, 
    Comment,
    Message,
    Tag,
    Vote,
    Word,
)

class PostView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    # Max distance around post is 1 kilometer
    MAX_DISTANCE = Decimal(1)

    def get_locations_nearby_coords(self, latitude, longitude, max_distance=None):
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
        if max_distance is not None:
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
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        text = self.request.query_params.get('text')
        timestamp = self.request.query_params.get('timestamp')
        location_description = self.request.query_params.get('location_description')
        # filter
        queryset = Post.objects.all()
        if latitude != None and longitude != None:
            queryset = self.get_locations_nearby_coords(
                latitude, longitude, max_distance=self.MAX_DISTANCE)
        if text != None:
            text_set = queryset.filter(text__contains=text)
            title_set = queryset.filter(title__contains=text)
            queryset = (text_set | title_set).distinct()
        if timestamp != None:
            queryset = queryset.filter(timestamp=timestamp)
        if location_description != None:
            loc_set = queryset.filter(location_description__isnull=False)
            queryset = loc_set.filter(
                location_description__contains=location_description)
        # order
        return queryset.annotate(
            vote_count=Avg('vote__rating', default=0)
            ).order_by('-vote_count')

class WordView(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = WordSerializer

    def get_queryset(self):
        # parameters
        text = self.request.query_params.get('text')
        # filter
        if text == None: return []
        return Word.objects.filter(text__contains=text
        ).annotate(post_count=Count('posts')
        ).filter(post_count__gt=0)

class CommentView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """
        Returns comments matching the post_id.
        """
        post_id = self.request.query_params.get('post_id')
        return Comment.objects.filter(post_id=post_id)

class VoteView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    serializer_class = VoteSerializer

    def get_queryset(self):
        """
        If parameters are missing, return all votes.
        Otherwise, return with username and post_id.
        """
        # parameters
        username = self.request.query_params.get("username")
        post_id = self.request.query_params.get("post_id")
        # filters
        if username == None or post_id == None:
            return Vote.objects.all()
        else:
            matching_users = User.objects.filter(username=username)
            if not matching_users: return Vote.objects.none()
            return Vote.objects.filter(voter=matching_users[0], post_id=post_id)

class FlagView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
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
    # permission_classes = (IsAuthenticated,)
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
    # permission_classes = (IsAuthenticated,)
    serializer_class = BlockSerializer

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
    # permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer

    def get_queryset(self):
        to_user = self.request.query_params.get("to_user")
        from_user = self.request.query_params.get("from_user")
        queryset = Message.objects.all()
        if to_user:
            queryset = queryset.filter(to_user=to_user)
        if from_user:
            queryset = queryset.filter(from_user=from_user)
        return queryset