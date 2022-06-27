from mist.permissions import MessagePermission
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.generics import get_user_from_request

from ..serializers import MessageSerializer
from ..models import Block, Message

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

class ConversationView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        requesting_user = get_user_from_request(request)

        conversations = {}

        blocking_users = Block.objects.filter(blocked_user=requesting_user)
        blocked_users = Block.objects.filter(blocking_user=requesting_user)
        cannot_message = blocking_users | blocked_users

        sent_messages = Message.objects.filter(sender=requesting_user)
        for sent_message in sent_messages:
            pk = sent_message.receiver.pk
            message_data = MessageSerializer(sent_message).data
            if blocking_users.filter(blocking_user_id=pk): continue
            if blocked_users.filter(blocked_user_id=pk): continue
            if pk not in conversations:
                conversations[pk] = []
            conversations[pk].append(message_data)

        received_messages = Message.objects.filter(receiver=requesting_user)
        for received_message in received_messages:
            if received_message.sender in cannot_message: continue
            pk = received_message.sender.pk
            message_data = MessageSerializer(received_message).data
            if blocking_users.filter(blocking_user_id=pk): continue
            if blocked_users.filter(blocked_user_id=pk): continue
            if pk not in conversations:
                conversations[pk] = []
            conversations[pk].append(message_data)

        return Response(conversations, status.HTTP_200_OK)