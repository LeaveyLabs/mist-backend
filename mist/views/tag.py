import string
from rest_framework import viewsets
from mist.permissions import TagPermission
from rest_framework.permissions import IsAuthenticated

from users.models import User

from ..models import Comment, Post, Tag
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
    
    def get_first_fifty_or_less_words(self, post_id):
        tagged_post = Post.objects.get(id=post_id)
        tagged_post_body = tagged_post.body
        tagged_post_words = tagged_post_body.split()
        first_fifty_words = tagged_post_words[:min(40, len(tagged_post_words))]
        last_word_with_punctuation = first_fifty_words[-1]
        first_fifty_words[-1] = last_word_with_punctuation.translate(
            str.maketrans('', '', string.punctuation))
        return first_fifty_words

    def create(self, request, *args, **kwargs):
        tag_response = super().create(request, *args, **kwargs)
        tagged_phone_number = tag_response.data.get("tagged_phone_number")
        tagging_user_id = tag_response.data.get("tagging_user")
        tagged_comment_id = tag_response.data.get('comment')

        if tagged_phone_number:
            tagging_user = User.objects.get(id=int(tagging_user_id))
            tagging_first_name = tagging_user.first_name
            tagging_last_name = tagging_user.last_name
            tagged_comment = Comment.objects.get(id=tagged_comment_id)
            tagged_post_snippet = " ".join(self.get_first_fifty_or_less_words(tagged_comment.post_id))
            download_link = "https://www.getmist.app/download"
            text_body = f"{tagging_first_name} {tagging_last_name} tagged you in a mist: \"{tagged_post_snippet}...\"\n\nSee what your secret admirer has to say about you: {download_link}"
            twilio_client.messages.create(
                to=tagged_phone_number,
                from_=twilio_phone_number,
                body=text_body,
            )
        return tag_response