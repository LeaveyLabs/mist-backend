from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ..serializers import FeatureSerializer
from ..models import Feature

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