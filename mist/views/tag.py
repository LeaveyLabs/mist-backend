from rest_framework import viewsets
from mist.permissions import TagPermission
from rest_framework.permissions import IsAuthenticated

from users.models import User

from ..models import Tag
from ..serializers import TagSerializer

import sys
sys.path.append("...")
from twilio_config import twilio_client, twilio_phone_number

class TagView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, TagPermission)
    serializer_class = TagSerializer

    def get_queryset(self):
        tagged_user = self.request.query_params.get("tagged_user")
        tagging_user = self.request.query_params.get("tagging_user")
        tagged_name = self.request.query_params.get("tagged_name")
        comment = self.request.query_params.get("comment")
        queryset = Tag.objects.all()
        if tagged_user:
            queryset = queryset.filter(tagged_user=tagged_user)
        if tagging_user:
            queryset = queryset.filter(tagging_user=tagging_user)
        if tagged_name:
            queryset = queryset.filter(tagged_name=tagged_name)
        if comment:
            queryset = queryset.filter(comment=comment)
        return queryset
    
    def create(self, request, *args, **kwargs):
        tag_response = super().create(request, *args, **kwargs)
        tagged_phone_number = tag_response.data.get("tagged_phone_number")
        tagging_user_id = tag_response.data.get("tagging_user")
        if tagged_phone_number:
            tagging_user = User.objects.get(id=int(tagging_user_id))
            tagging_first_name = tagging_user.first_name
            tagging_last_name = tagging_user.last_name
            download_link = "https://www.getmist.app/download"
            text_body = f"{tagging_first_name} {tagging_last_name} tagged you in a mist...\n\nSee what your secret admirer has to say about you: {download_link}"
            twilio_client.messages.create(
                to=tagged_phone_number,
                from_=twilio_phone_number,
                body=text_body,
            )
        return tag_response