import logging
from typing import Any

import environ
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from huey.contrib.djhuey import db_task, lock_task

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
from application.core.services.security_gate import check_security_gate

logger = logging.getLogger("secobserve.core")


@receiver(pre_save, sender=Observation)
def observation_pre_save(sender: Any, instance: Observation, **kwargs: Any) -> None:  # pylint: disable=unused-argument
    # sender is needed according to Django documentation
    normalize_observation_fields(instance)
    instance.identity_hash = get_identity_hash(instance)
    set_product_flags(instance)


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
        if instance.is_product_group:
            for product in instance.products.all():
                check_security_gate(product)
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
    set_default_branch(instance)


@receiver(post_save, sender=Settings)
def settings_post_save(  # pylint: disable=unused-argument
    sender: Any, instance: Settings, created: bool, **kwargs: Any
) -> None:
    # parameters are needed according to Django documentation
    env = environ.Env()
    if not env.bool("SO_UNITTESTS", False):
        settings_post_save_task()


@db_task()
@lock_task("product_settings_post_save_task_lock")
def settings_post_save_task() -> None:

    logger.info("--- Settings post_save_task - start ---")

    for product in Product.objects.filter(is_product_group=False):
        check_security_gate(product)

    logger.info("--- Settings post_save_task - finished ---")
