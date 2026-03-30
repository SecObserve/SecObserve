from typing import Any
from django.utils import timezone

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from application.access_control.services.current_user import get_current_user
from application.licenses.models import (
    License_Component,
    License_Group,
    License_Group_Member,
    License_Policy,
    License_Policy_Member,
)


@receiver(post_save, sender=License_Group)
def license_group_post_save(  # pylint: disable=unused-argument
    sender: Any, instance: License_Group, created: bool, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    if created:
        user = get_current_user()
        if user and not user.is_superuser:
            License_Group_Member.objects.update_or_create(license_group=instance, user=user, is_manager=True)


@receiver(post_save, sender=License_Policy)
def license_policy_post_save(  # pylint: disable=unused-argument
    sender: Any, instance: License_Policy, created: bool, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    if created:
        user = get_current_user()
        if user and not user.is_superuser:
            License_Policy_Member.objects.update_or_create(license_policy=instance, user=user, is_manager=True)


@receiver(post_save, sender=License_Component)
def license_component_post_save(  # pylint: disable=unused-argument
    sender: Any, instance: License_Component, created: bool, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    if created or "evaluation_result" in instance.get_dirty_fields().keys():
        instance.product.last_license_change = timezone.now()
        instance.product.save()


@receiver(post_delete, sender=License_Component)
def license_component_post_delete(  # pylint: disable=unused-argument
    sender: Any, instance: License_Component, **kwargs: Any
) -> None:
    instance.product.last_license_change = timezone.now()
    instance.product.save()
