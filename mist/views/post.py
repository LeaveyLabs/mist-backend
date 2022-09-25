from decimal import Decimal
from enum import Enum
import math
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db.models.expressions import RawSQL
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from mist.permissions import PostPermission
from rest_framework.permissions import IsAuthenticated

from users.generics import get_user_from_request

from ..serializers import MistboxSerializer, PostSerializer
from ..models import Feature, FriendRequest, MatchRequest, Mistbox, Post, Tag, get_current_time

class Order(Enum):
    RECENT = 0
    BEST = 1
    TRENDING = 2

    def recent(post):
        return post.timestamp

    def votecount(post):
        return sum([vote.rating for vote in post.votes.all()])

    def commentcount(post):
        return post.comments.count()
    
    def flagcount(post):
        return sum([flag.rating for flag in post.flags.all()])

    def trendscore(post):
        NORM_CONSTANT = 100000
        try: post.viewcount
        except: post.viewcount = 0
        return sum(
            [vote.rating*
            math.pow(2, (post.timestamp-get_current_time())/NORM_CONSTANT)*
            (1/(post.viewcount+1))
            for vote in post.votes.all()])

    def permissible_post(post):
        if Order.flagcount(post) < 2: return True
        return Order.votecount(post)*Order.votecount(post) >= Order.flagcount(post)

class PostView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, PostPermission,)
    serializer_class = PostSerializer

    # Max distance around post is 5 kilometers
    MAX_DISTANCE = Decimal(5)

    def list(self, request, *args, **kwargs):
        user = get_user_from_request(request)

        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.\
            prefetch_related("votes", "comments", "flags", "views").\
            annotate(viewcount=Count("views", filter=Q(views__user=user)))
       
        queryset = self.order_queryset(queryset)
        queryset = self.custom_paginate_queryset(queryset)
        queryset = self.remove_impermissible_posts(queryset)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def custom_paginate_queryset(self, queryset):
        page = self.request.query_params.get('page')
        order = self.request.query_params.get('order')
        paginator = Paginator(queryset, 100)
        try:
            page_num = int(page)
            if page_num > 0: return paginator.page(page_num).object_list
            else: return paginator.page(1).object_list
        except:
            if not order: return queryset
            return paginator.page(1).object_list

    def order_queryset(self, queryset):
        order = self.request.query_params.get('order')

        try:
            order_num = int(order)
            if order_num == Order.BEST.value:
                return sorted(queryset, key=Order.votecount, reverse=True)
            elif order_num == Order.RECENT.value:
                return sorted(queryset, key=Order.recent, reverse=True)
            else:
                return sorted(queryset, key=Order.trendscore, reverse=True)
        except:
            return sorted(queryset, key=Order.trendscore, reverse=True)

    def remove_impermissible_posts(self, queryset):
        return filter(Order.permissible_post, queryset)

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
            if radius:
                queryset = self.get_locations_nearby_coords(
                    latitude, longitude, radius)
            else: 
                queryset = self.get_locations_nearby_coords(
                    latitude, longitude)
        if ids:
            queryset = queryset.filter(pk__in=ids)
        if words:
            q = Q()
            for word in words:
                q |= Q(title__icontains=word)
                q |= Q(body__icontains=word)
                q |= Q(location_description__icontains=word)
            queryset = Post.objects.filter(q)
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
        
        return queryset.\
            prefetch_related("votes", "comments", "flags")

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


class MatchedPostsView(PostView):
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
        matched_posts = Post.objects.filter(
            pk__in=matched_post_pks).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-creation_time')
        return matched_posts


class FeaturedPostsView(PostView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        featured_post_pks = Feature.objects.values_list('post')
        featured_posts = Post.objects.filter(
            pk__in=featured_post_pks).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-creation_time')
        return featured_posts


class FriendPostsView(PostView):
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
        return Post.objects.filter(author_id__in=friend_pks).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-creation_time')


class FavoritedPostsView(PostView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        return Post.objects.filter(favorite__favoriting_user=user).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-creation_time')


class SubmittedPostsView(PostView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        return Post.objects.filter(author=user).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-creation_time')

class TaggedPostsView(PostView):
    permission_classes = (IsAuthenticated, )
    serializer_class = PostSerializer

    def get_queryset(self):
        user = get_user_from_request(self.request)
        tags = Tag.objects.filter(tagged_user=user)
        if user.phone_number:
            tagged_numbers = Tag.objects.filter(tagged_phone_number=user.phone_number)
            tags = (tags | tagged_numbers).distinct()
        tagged_posts = Post.objects.filter(comments__tags__in=tags).\
            prefetch_related("votes", "comments", "flags").\
            order_by('-comments__tags__timestamp')
        return tagged_posts

class MistboxView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = MistboxSerializer

    def retrieve(self, request, *args, **kwargs):
        mistbox = self.get_object()
        user = get_user_from_request(request)
        
        self.filter_mistbox_posts(mistbox, user)

        serializer = self.get_serializer(mistbox)
        return Response(serializer.data)

    def filter_mistbox_posts(self, mistbox, user):
        mistbox.posts.set(
            sorted(
                mistbox.posts.exclude(
                    views__user=user
                ).all(),
                key=Order.recent,
            )
        )

    def get_object(self):
        user = get_user_from_request(self.request)
        return get_object_or_404(
            Mistbox.objects.all().prefetch_related('posts'),
            user=user,
        )

    def partial_update(self, request, *args, **kwargs):
        mistbox_updates = MistboxSerializer(data=request.data)
        mistbox_updates.is_valid(raise_exception=True)

        user = get_user_from_request(self.request)

        mistbox, _ = Mistbox.objects.get_or_create(user=user)
        mistbox.keywords = mistbox_updates.data.get('keywords')
        mistbox.save()

        return Response(
            {
                "status": "success",
                "data": mistbox_updates.data,
            },
            status.HTTP_200_OK)

class DeleteMistboxPostView(generics.DestroyAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = MistboxSerializer

    def destroy(self, request, *args, **kwargs):
        user = get_user_from_request(self.request)
        post_id = self.request.query_params.get("post")
        opened = self.request.query_params.get("opened")

        post = get_object_or_404(
            Post.objects.all(),
            id=post_id,
        )
        mistbox = get_object_or_404(
            Mistbox.objects.all(),
            user=user,
        )

        if post not in mistbox.posts.all():
            return Response(None, status.HTTP_404_NOT_FOUND)
        
        mistbox.posts.remove(post)

        if opened: mistbox.opens_used_today += 1

        if opened and mistbox.opens_used_today + 1 > Mistbox.MAX_DAILY_SWIPES:
            return Response(
            {
                "detail": "no opens left today"
            }, 
            status.HTTP_400_BAD_REQUEST)

        mistbox.save()
        
        return Response(None, status.HTTP_204_NO_CONTENT)