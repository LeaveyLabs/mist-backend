from rest_framework import viewsets
from mist.permissions import TagPermission
from rest_framework.permissions import IsAuthenticated

from ..serializers import TagSerializer
from ..models import Tag

class TagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, TagPermission)
    serializer_class = TagSerializer

    def get_queryset(self):
        tagged_user = self.request.query_params.get("tagged_user")
        tagging_user = self.request.query_params.get("tagging_user")
        comment = self.request.query_params.get("comment")
        queryset = Tag.objects.all()
        if tagged_user:
            queryset = queryset.filter(tagged_user=tagged_user)
        if tagging_user:
            queryset = queryset.filter(tagging_user=tagging_user)
        if comment:
            queryset = queryset.filter(comment=comment)
        return queryset