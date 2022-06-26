from rest_framework import viewsets
from mist.permissions import FlagPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import FlagSerializer
from ..models import Flag

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