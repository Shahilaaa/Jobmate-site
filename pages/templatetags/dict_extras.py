from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allow dict[key] access in Django templates: {{ mydict|get_item:key }}"""
    return dictionary.get(key, 0)


@register.filter
def smart_deadline(value):
    """
    Display a deadline smartly:
    - If it's within the next 24 hours → "In Xh Ym"  (urgent)
    - If it's within today             → "Today HH:MM"
    - If it's a past datetime          → "Overdue – j M Y"
    - Otherwise                        → "j M Y"
    """
    if not value:
        return "—"
    now = timezone.now()
    try:
        # If value is date-only (not datetime), make naive datetime then make aware
        from datetime import datetime as _dt, date as _d
        if isinstance(value, _d) and not isinstance(value, _dt):
            from django.utils.timezone import make_aware
            value = make_aware(_dt.combine(value, _dt.min.time().replace(hour=23, minute=59)))
        diff = value - now
        total_secs = diff.total_seconds()
        if total_secs < 0:
            return f"Overdue — {value.strftime('%-d %b %Y')}"
        elif total_secs <= 86400:  # within 24 hours
            h = int(total_secs // 3600)
            m = int((total_secs % 3600) // 60)
            if h == 0:
                return f"⚡ In {m}m"
            return f"⚡ In {h}h {m}m"
        else:
            return value.strftime("%-d %b %Y")
    except Exception:
        return str(value)


@register.filter
def deadline_urgency(value):
    """Returns CSS class string: 'urgent' if <24h, 'overdue' if past, '' otherwise."""
    if not value:
        return ""
    try:
        from datetime import datetime as _dt, date as _d
        now = timezone.now()
        if isinstance(value, _d) and not isinstance(value, _dt):
            from django.utils.timezone import make_aware
            value = make_aware(_dt.combine(value, _dt.min.time().replace(hour=23, minute=59)))
        diff = (value - now).total_seconds()
        if diff < 0:
            return "overdue"
        elif diff <= 86400:
            return "urgent"
        return ""
    except Exception:
        return ""
