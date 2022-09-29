from django.db.models import Q
from push_notifications.models import APNSDevice
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mist.permissions import MessagePermission
from users.generics import get_user_from_request
from users.models import UserNotification, User

from ..serializers import MessageSerializer
from ..models import MatchRequest, Message

class MessageView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, MessagePermission)
    serializer_class = MessageSerializer

    def get_queryset(self):
        sender = self.request.query_params.get("sender")
        receiver = self.request.query_params.get("receiver")
        queryset = Message.objects.all()
        if receiver:
            queryset = queryset.filter(receiver=receiver)
        if sender:
            queryset = queryset.filter(sender=sender)
        return queryset
    
    def create(self, request, *args, **kwargs):
        message_response = super().create(request, *args, **kwargs)
        sender = message_response.data.get("sender")
        receiver = message_response.data.get("receiver")
        body = message_response.data.get("body")

        sender_match_request = MatchRequest.objects.filter(
            match_requesting_user=sender,
            match_requested_user=receiver
        )
        receiver_match_request = MatchRequest.objects.filter(
            match_requesting_user=receiver,
            match_requested_user=sender,
        )

        if sender_match_request.exists() and receiver_match_request.exists():
            username = User.objects.get(id=sender).username
            UserNotification.objects.create(
                user_id=receiver,
                type=UserNotification.NotificationTypes.MESSAGE,
                data=message_response.data,
                message=f"{username}: {body}",
            )
        
        return message_response

class ConversationView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        requesting_user = get_user_from_request(request)

        conversations = {}

        sender_or_receiver_query = Q(sender=requesting_user) | Q(receiver=requesting_user)
        exclude_blocks_query = \
            Q(sender__blockings__blocked_user=requesting_user) | \
            Q(receiver__blockings__blocked_user=requesting_user) | \
            Q(sender__blocks__blocking_user=requesting_user) | \
            Q(receiver__blocks__blocking_user=requesting_user)
        exclude_hidden_query = Q(is_hidden=True)

        sent_or_received_messages = Message.objects.\
            filter(sender_or_receiver_query).\
            exclude(exclude_blocks_query).\
            exclude(exclude_hidden_query).\
            select_related('receiver').\
            select_related('sender')
            
        for message in sent_or_received_messages:
            opposite_pk = None

            if requesting_user == message.sender:
                opposite_pk = message.receiver.pk
            else:
                opposite_pk = message.sender.pk

            if opposite_pk not in conversations:
                conversations[opposite_pk] = []
            
            message_data = MessageSerializer(message).data
            conversations[opposite_pk].append(message_data)

        return Response(conversations, status.HTTP_200_OK)