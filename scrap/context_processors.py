from .models import Notification

def notifications_context(request):
    """Injects notification data into every template context."""
    if request.user.is_authenticated:
        nav_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return {
            'nav_notifications': nav_notifications,
            'nav_unread_count': unread_count,
        }
    return {}
