import django.core.validators
from django.db import migrations, models
from django.utils import timezone

CRONTABS = [
    "background_epss_import",
    "branch_housekeeping",
    "risk_acceptance_expiry",
    "api_import",
    "license_import",
]


def shift_crontab(hour: int, minute: int, offset_minutes: int) -> tuple[int, int]:
    return divmod((hour * 60 + minute + offset_minutes) % (24 * 60), 60)


def _shift_crontabs(apps, sign: int) -> None:
    # Offset at migration time: with DST, the runs move by an hour in the other half of the year
    offset_minutes = sign * int(timezone.localtime().utcoffset().total_seconds() // 60)
    if not offset_minutes:
        return

    Settings = apps.get_model("commons", "Settings")
    for settings in Settings.objects.all():
        for crontab in CRONTABS:
            hour, minute = shift_crontab(
                getattr(settings, f"{crontab}_crontab_hour"),
                getattr(settings, f"{crontab}_crontab_minute"),
                offset_minutes,
            )
            setattr(settings, f"{crontab}_crontab_hour", hour)
            setattr(settings, f"{crontab}_crontab_minute", minute)
        settings.save()


def crontabs_from_utc_to_server_time_zone(apps, schema_editor):
    _shift_crontabs(apps, 1)


def crontabs_from_server_time_zone_to_utc(apps, schema_editor):
    _shift_crontabs(apps, -1)


class Migration(migrations.Migration):

    dependencies = [
        ("commons", "0027_settings_oidc_api_token_max_authentication_age"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="api_import_crontab_hour",
            field=models.IntegerField(
                default=4,
                help_text="Hour crontab expression for API imports (server time zone)",
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)],
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="background_epss_import_crontab_hour",
            field=models.IntegerField(
                default=3,
                help_text="Hour crontab expression for EPSS import (server time zone)",
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)],
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="branch_housekeeping_crontab_hour",
            field=models.IntegerField(
                default=2,
                help_text="Hour crontab expression for branch housekeeping (server time zone)",
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)],
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="license_import_crontab_hour",
            field=models.IntegerField(
                default=1,
                help_text="Hour crontab expression for importing licenses (server time zone)",
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)],
            ),
        ),
        migrations.AlterField(
            model_name="settings",
            name="risk_acceptance_expiry_crontab_hour",
            field=models.IntegerField(
                default=1,
                help_text="Hour crontab expression for checking risk acceptance expiry (server time zone)",
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(23)],
            ),
        ),
        migrations.RunPython(
            crontabs_from_utc_to_server_time_zone,
            reverse_code=crontabs_from_server_time_zone_to_utc,
        ),
    ]
