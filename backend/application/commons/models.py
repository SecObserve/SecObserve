from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    BooleanField,
    CharField,
    IntegerField,
    Model,
)

from application.commons.services.request_cache import cache_for_request
from application.commons.types import VEX_Justification_Styles


class Settings(Model):
    security_gate_active = BooleanField(default=True, help_text="Is the security gate activated?")
    security_gate_threshold_critical = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of critical observations that must not be exceeded",
    )
    security_gate_threshold_high = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of high observations that must not be exceeded",
    )
    security_gate_threshold_medium = IntegerField(
        default=99999,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of medium observations that must not be exceeded",
    )
    security_gate_threshold_low = IntegerField(
        default=99999,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of low observations that must not be exceeded",
    )
    security_gate_threshold_none = IntegerField(
        default=99999,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of none observations that must not be exceeded",
    )
    security_gate_threshold_unknown = IntegerField(
        default=99999,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Number of unknown observations that must not be exceeded",
    )

    jwt_validity_duration_user = IntegerField(
        default=168,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Validity duration of JWT tokens for regular users in hours",
    )
    jwt_validity_duration_superuser = IntegerField(
        default=24,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Validity duration of JWT tokens for superusers in hours",
    )
    internal_users = CharField(
        max_length=255,
        blank=True,
        help_text="Comma separated list of email regular expressions to identify internal users",
    )

    base_url_frontend = CharField(
        max_length=255,
        default="",
        help_text="Base URL of the frontend, used to set links in notifications correctly",
    )

    exception_ms_teams_webhook = CharField(
        max_length=255,
        blank=True,
        help_text="MS Teams webhook to send exception notifications",
    )
    exception_slack_webhook = CharField(
        max_length=255,
        blank=True,
        help_text="Slack webhook to send exception notifications",
    )
    exception_rate_limit = IntegerField(
        default=3600,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Timedelta in seconds when to send the same exception the next time",
    )
    email_from = CharField(
        max_length=255,
        blank=True,
        help_text="From address for sending email notifications",
    )
    exception_email_to = CharField(
        max_length=255,
        blank=True,
        help_text="Comma separated email addresses to send exception notifications",
    )

    background_product_metrics_interval_minutes = IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Calculate product metrics every x minutes",
    )
    background_epss_import_crontab_minute = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        help_text="Minute crontab expression for EPSS import",
    )
    background_epss_import_crontab_hour = IntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour crontab expression for EPSS import (UTC)",
    )

    branch_housekeeping_crontab_minute = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        help_text="Minute crontab expression for branch housekeeping",
    )
    branch_housekeeping_crontab_hour = IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour crontab expression for branch housekeeping (UTC)",
    )
    branch_housekeeping_active = BooleanField(default=True, help_text="Delete inactive branches")
    branch_housekeeping_keep_inactive_days = IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Days before incative branches and their observations are deleted",
    )
    branch_housekeeping_exempt_branches = CharField(
        max_length=255,
        blank=True,
        help_text="Regular expression which branches to exempt from deletion",
    )

    feature_vex = BooleanField(default=False, help_text="Export and import VEX documents in various formats")
    vex_justification_style = CharField(
        max_length=16,
        choices=VEX_Justification_Styles.STYLE_CHOICES,
        default=VEX_Justification_Styles.STYLE_CSAF_OPENVEX,
    )

    feature_disable_user_login = BooleanField(default=False, help_text="Disable user login")
    feature_general_rules_need_approval = BooleanField(default=False, help_text="General rules need approval")

    risk_acceptance_expiry_days = IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Days before risk acceptance expires, 0 means no expiry",
    )
    risk_acceptance_expiry_crontab_minute = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        help_text="Minute crontab expression for checking risk acceptance expiry",
    )
    risk_acceptance_expiry_crontab_hour = IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour crontab expression for checking risk acceptance expiry (UTC)",
    )

    feature_automatic_api_import = BooleanField(default=True, help_text="Enable automatic API imports")
    api_import_crontab_minute = IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        help_text="Minute crontab expression for API imports",
    )
    api_import_crontab_hour = IntegerField(
        default=4,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour crontab expression for API imports (UTC)",
    )

    password_validator_minimum_length = IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(4096)],
        help_text="Validates that the password is of a minimum length.",
    )
    password_validator_attribute_similarity = BooleanField(
        default=True,
        help_text="Validates that the password is sufficiently different from certain attributes of the user.",
    )
    password_validator_common_passwords = BooleanField(
        default=True, help_text="Validates that the password is not a common password."
    )
    password_validator_not_numeric = BooleanField(
        default=True, help_text="Validate that the password is not entirely numeric."
    )

    feature_license_management = BooleanField(default=True, help_text="Enable license management")
    license_import_crontab_minute = IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        help_text="Minute crontab expression for importing licenses",
    )
    license_import_crontab_hour = IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour crontab expression for importing licenses (UTC)",
    )
    feature_automatic_osv_scanning = BooleanField(default=True, help_text="Enable automatic OSV scanning")
    feature_exploit_information = BooleanField(default=True, help_text="Enable CVSS enrichment")
    exploit_information_max_age_years = IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(999999)],
        help_text="Maximum age of CVEs for enrichment in years",
    )
    periodic_task_max_entries = IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(999999)],
        help_text="Maximum number of entries to keep per periodic task",
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Save object to the database. Removes all other entries if there
        are any.
        """
        self.__class__.objects.exclude(id=self.pk).delete()
        super().save(*args, **kwargs)

    @classmethod
    @cache_for_request
    def load(cls) -> "Settings":
        """
        Load object from the database. Failing that, create a new empty
        (default) instance of the object and return it (without saving it
        to the database).
        """
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()
