from django.shortcuts import get_object_or_404
from push_notifications.models import APNSDevice
from rest_framework import viewsets
from mist.permissions import MatchRequestPermission
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from users.generics import get_user_from_request
from users.models import User

from ..serializers import MatchRequestSerializer, ReadOnlyUserSerializer
from ..models import MatchRequest, NotificationTypes

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

    def create(self, request, *args, **kwargs):
        match_request_response = super().create(request, *args, **kwargs)
        match_requested_user = match_request_response.data.get("match_requested_user")
        if not MatchRequest.objects.filter(
            match_requesting_user=match_requested_user).exists():
            receiving_devices = APNSDevice.objects.filter(user=match_requested_user)
            receiving_devices.send_message(
                "someone replied to your mist 👀",
                extra={
                    "type": NotificationTypes.MATCH,
                    "data": match_request_response.data
                })
        return match_request_response

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
