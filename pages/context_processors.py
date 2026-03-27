from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}
    try:
        return {"unread_notifications": Notification.objects.filter(user=request.user, is_read=False).count()}
    except Exception:
        return {"unread_notifications": 0}


def user_avatar_context(request):
    """Provide current user's profile image URL, background image URL and initials."""
    if not request.user.is_authenticated:
        return {"current_user_avatar_url": None, "current_user_bg_url": None, "current_user_initials": "?"}
    try:
        user = request.user
        initials = (
            (user.first_name[:1] + user.last_name[:1]).upper()
            if user.first_name else user.username[:2].upper()
        )
        avatar_url = None
        bg_url = None
        if hasattr(user, 'profile'):
            role = user.profile.role
            if role == 'employee' and hasattr(user.profile, 'employee'):
                emp = user.profile.employee
                if emp.profile_image:
                    avatar_url = emp.profile_image.url
                if emp.background_image:
                    bg_url = emp.background_image.url
            elif role == 'client' and hasattr(user.profile, 'client'):
                cli = user.profile.client
                if hasattr(cli, 'profile_image') and cli.profile_image:
                    avatar_url = cli.profile_image.url
                if hasattr(cli, 'background_image') and cli.background_image:
                    bg_url = cli.background_image.url
        return {
            "current_user_avatar_url": avatar_url,
            "current_user_bg_url": bg_url,
            "current_user_initials": initials,
        }
    except Exception:
        return {"current_user_avatar_url": None, "current_user_bg_url": None, "current_user_initials": "?"}
