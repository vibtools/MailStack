from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserAccessPolicy


@receiver(post_save, sender=get_user_model())
def ensure_access_policy(sender, instance, created, **kwargs) -> None:  # noqa: ARG001
    UserAccessPolicy.objects.get_or_create(user=instance)
