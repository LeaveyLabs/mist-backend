from rest_framework import viewsets
from mist.permissions import FlagPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import CommentFlagSerializer
from ..models import CommentFlag

class CommentFlagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, FlagPermission)
    serializer_class = CommentFlagSerializer

    def get_queryset(self):
        flagger = self.request.query_params.get("flagger")
        comment = self.request.query_params.get("comment")
        queryset = CommentFlag.objects.all()
        if flagger:
            queryset = queryset.filter(flagger=flagger)
        if comment:
            queryset = queryset.filter(comment=comment)
        return queryset