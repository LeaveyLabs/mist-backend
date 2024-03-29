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
    UserNotification
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

        if notification_type == UserNotification.NotificationTypes.MESSAGE:
            notification_query = Q(
                sangdaebang=sangdaebang,
                user=user, 
                type=notification_type, 
                timestamp__lte=timestamp)
    
        UserNotification.objects.\
            filter(notification_query).\
            update(has_been_seen=True)
        
        user.notification_badges_enabled = True
        user.save()
        
        UserNotification.update_badges(user)
        
        return Response(
            {
                "status": "success",
                "data": message_activity.data,
            },
            status=status.HTTP_200_OK)

class LastOpenedNotificationTime(generics.RetrieveAPIView):
    def retrieve(self, *args, **kwargs):
        type = self.request.query_params.get('type')
        sangdaebang = self.request.query_params.get('sangdaebang')

        opened_notifications = UserNotification.objects.\
            filter(type=type, sangdaebang=sangdaebang).\
            order_by('-timestamp')
        
        if not opened_notifications.exists():
            return Response(
            {
                "timestamp": 0,
            }, 
            status=status.HTTP_200_OK)
        
        return Response(
        {
            "timestamp": opened_notifications[0].timestamp,
        }, 
        status=status.HTTP_200_OK)