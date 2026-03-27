from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, UserRole

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Ensure every User has a Profile. Role and sub-profiles are set by RegisterForm.save()."""
    if created:
        Profile.objects.get_or_create(user=instance, defaults={"role": UserRole.CLIENT})
