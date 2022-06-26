from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics
from mist.permissions import FriendRequestPermission
from rest_framework.permissions import IsAuthenticated
from users.generics import get_user_from_request
from users.models import User

from users.serializers import ReadOnlyUserSerializer

from ..serializers import FriendRequestSerializer
from ..models import FriendRequest


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