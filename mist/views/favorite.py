from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from mist.permissions import FavoritePermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import FavoriteSerializer

from ..models import Favorite

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