class NotificationServiceMock:
    sent_notifications = []
    badges = 0

    def send_fake_notification(self, message, badge, *args, **kwargs):
        NotificationServiceMock.badges = badge
        NotificationServiceMock.sent_notifications.append(message)