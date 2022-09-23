from django.db.models import Q
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.generics import get_user_from_request

from ..serializers import (
    OpenedNotificationSerializer
)
from ..models import (
    Notification
)

class OpenNotifications(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )
    
    def create(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        request_copy = request.data.copy()        
        request_copy.update({"user": user.id})

        message_activity = OpenedNotificationSerializer(data=request_copy)
        message_activity.is_valid(raise_exception=True)

        timestamp = message_activity.data.get('timestamp')
        sangdaebang = message_activity.data.get('sangdaebang')
        notification_type = message_activity.data.get('type')

        notification_query = Q(user=user, type=notification_type, timestamp__lte=timestamp)

        if notification_type == Notification.NotificationTypes.MESSAGE:
            notification_query = Q(
                sangdaebang=sangdaebang,
                user=user, 
                type=notification_type, 
                timestamp__lte=timestamp)
    
        Notification.objects.\
            filter(notification_query).\
            update(has_been_seen=True)
        
        user.notification_badges_enabled = True
        user.save()
        
        Notification.update_badges(user)
        
        return Response(
            {
                "status": "success",
                "data": message_activity.data,
            },
            status=status.HTTP_200_OK)