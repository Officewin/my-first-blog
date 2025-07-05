from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserAppAccess(models.Model):
    """Store which pronunciation apps a user can access."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="app_access")
    pronounce_advanced = models.BooleanField(default=False)
    pronounce_easy = models.BooleanField(default=False)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.user.username


@receiver(post_save, sender=User)
def create_user_app_access(sender, instance, created, **kwargs):
    if created:
        UserAppAccess.objects.create(user=instance)
