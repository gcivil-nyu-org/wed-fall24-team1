def notifications_processor(request):
    if request.user.is_authenticated:
        notifications = request.user.notifications.order_by('-created_at')[:5]
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        return {
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count
        }
    return {}