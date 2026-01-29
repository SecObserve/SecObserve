from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateField,
    ForeignKey,
    Index,
    ManyToManyField,
    Model,
)
from encrypted_model_fields.fields import EncryptedCharField

from application.access_control.types import (
    ListSize,
    MetricsTimespan,
    PackageInfo,
    Theme,
)


class User(AbstractUser):
    full_name = CharField(max_length=301, blank=True)
    is_external = BooleanField(default=False)
    setting_theme = CharField(max_length=6, choices=Theme.THEME_CHOICES, default=Theme.THEME_LIGHT)
    setting_list_size = CharField(max_length=6, choices=ListSize.LIST_SIZE_CHOICES, default=ListSize.LIST_SIZE_MEDIUM)
    setting_package_info_preference = CharField(
        max_length=20,
        choices=PackageInfo.PACKAGE_INFO_PREFERENCE_CHOICES,
        default=PackageInfo.PACKAGE_INFO_PREFERENCE_DEPS_DEV,
    )
    setting_metrics_timespan = CharField(
        max_length=8, choices=MetricsTimespan.METRICS_TIMESPAN_CHOICES, default=MetricsTimespan.METRICS_TIMESPAN_7_DAYS
    )
    oidc_groups_hash = CharField(max_length=64, blank=True)
    is_oidc_user = BooleanField(default=False)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        elif self.first_name:
            self.full_name = self.first_name
        elif self.last_name:
            self.full_name = self.last_name
        elif not self.full_name:
            self.full_name = self.username

        super().save(*args, **kwargs)


class Authorization_Group(Model):
    name = CharField(max_length=255, unique=True)
    oidc_group = CharField(max_length=255, blank=True)
    users: ManyToManyField = ManyToManyField(
        User,
        through="Authorization_Group_Member",
        related_name="authorization_groups",
        blank=True,
    )

    class Meta:
        verbose_name = "Authorization Group"
        verbose_name_plural = "Authorization Groups"
        indexes = [
            Index(fields=["oidc_group"]),
        ]

    def __str__(self) -> str:
        return self.name


class Authorization_Group_Member(Model):
    authorization_group = ForeignKey(Authorization_Group, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    is_manager = BooleanField(default=False)

    class Meta:
        unique_together = (
            "authorization_group",
            "user",
        )

    def __str__(self) -> str:
        return f"{self.authorization_group} / {self.user}"


class JWT_Secret(Model):
    secret = EncryptedCharField(max_length=255)

    class Meta:
        verbose_name = "JWT secret"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save object to the database. Removes all other entries if there
        are any.
        """
        self.__class__.objects.exclude(id=self.pk).delete()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "JWT_Secret":
        """
        Load object from the database. Failing that, create a new empty
        (default) instance of the object and return it (without saving it
        to the database).
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class API_Token(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    name = CharField(max_length=32, default="default")
    api_token_hash = CharField(max_length=255)
    expiration_date = DateField(null=True)

    class Meta:
        verbose_name = "API token"
        verbose_name_plural = "API token"
        unique_together = (
            "user",
            "name",
        )


class API_Token_Multiple(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    name = CharField(max_length=32, default="default")
    api_token_hash = CharField(max_length=255)
    expiration_date = DateField(null=True)

    class Meta:
        verbose_name = "API token"
        verbose_name_plural = "API token"
        unique_together = (
            "user",
            "name",
        )
