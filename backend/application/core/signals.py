import logging
from typing import Any

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from huey.contrib.djhuey import lock_task, on_commit_task

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.authorization.services.roles_permissions import Roles
from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Product_Member
from application.core.services.branch import set_default_branch
from application.core.services.observation import (
    get_identity_hash,
    normalize_observation_fields,
    set_product_flags,
)
from application.core.services.security_gate import (
    SECURITY_GATE_FIELDS,
    check_security_gate,
    check_security_gates,
)
from application.issue_tracker.services.issue_tracker import (
    push_deleted_observation_to_issue_tracker,
)

logger = logging.getLogger("secobserve.core")


@receiver(pre_save, sender=Observation)
def observation_pre_save(sender: Any, instance: Observation, **kwargs: Any) -> None:  # pylint: disable=unused-argument
    # sender is needed according to Django documentation
    normalize_observation_fields(instance)
    instance.identity_hash = get_identity_hash(instance)
    set_product_flags(instance)


@receiver(post_delete, sender=Observation)
def observation_post_delete(
    sender: Any, instance: Observation, **kwargs: Any  # pylint: disable=unused-argument
) -> None:
    # sender is needed according to Django documentation
    product = instance.product
    issue_tracker_issue_id = instance.issue_tracker_issue_id
    user = get_current_user()
    transaction.on_commit(lambda: push_deleted_observation_to_issue_tracker(product, issue_tracker_issue_id, user))


@receiver(post_delete, sender=Product)
def product_post_delete(sender: Any, instance: Product, **kwargs: Any) -> None:  # pylint: disable=unused-argument
    # sender is needed according to Django documentation
    User.objects.filter(username__startswith=f"-product-{instance.pk}-").delete()


@receiver(post_save, sender=Product)
def product_post_save(
    sender: Any, instance: Product, created: bool, **kwargs: Any  # pylint: disable=unused-argument
) -> None:
    # sender is needed according to Django documentation
    if not created:
        dirty_fields = instance.get_dirty_fields().keys()
        if any(field in dirty_fields for field in SECURITY_GATE_FIELDS):
            if instance.is_product_group:
                check_security_gates(instance.products.all())
            else:
                check_security_gate(instance)
    else:
        user = get_current_user()
        if user:
            Product_Member(product=instance, user=user, role=Roles.Owner).save()


@receiver(post_save, sender=Branch)
def branch_post_save(
    sender: Any, instance: Branch, created: bool, **kwargs: Any  # pylint: disable=unused-argument
) -> None:
    # sender is needed according to Django documentation
    set_default_branch(instance, created)


@receiver(post_save, sender=Settings)
def settings_post_save(  # pylint: disable=unused-argument
    sender: Any, instance: Settings, created: bool, **kwargs: Any
) -> None:
    # parameters are needed according to Django documentation
    dirty_fields = instance.get_dirty_fields().keys()
    if any(field in dirty_fields for field in SECURITY_GATE_FIELDS):
        settings_post_save_task()


@on_commit_task()
@lock_task("product_settings_post_save_task_lock")
def settings_post_save_task() -> None:

    logger.info("--- Settings post_save_task - start ---")

    # Products with a security gate of their own or of their product group don't use the settings
    check_security_gates(
        Product.objects.filter(is_product_group=False, security_gate_active__isnull=True).filter(
            Q(product_group__isnull=True) | Q(product_group__security_gate_active__isnull=True)
        )
    )

    logger.info("--- Settings post_save_task - finished ---")
