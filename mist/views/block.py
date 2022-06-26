from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from mist.permissions import BlockPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import BlockSerializer
from ..models import Block

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