from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("licenses", "0025_license_component_url_copyright"),
    ]

    operations = [
        migrations.AddField(
            model_name="license",
            name="scancode_key",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="license",
            name="scancode_category",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="license",
            name="scancode_owner",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="license",
            name="scancode_homepage_url",
            field=models.CharField(blank=True, max_length=2048),
        ),
        migrations.AddField(
            model_name="license",
            name="scancode_faq_url",
            field=models.CharField(blank=True, max_length=2048),
        ),
        migrations.AddField(
            model_name="license",
            name="scancode_text_urls",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="license",
            name="choosealicense_key",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="license",
            name="choosealicense_description",
            field=models.TextField(blank=True, max_length=2048),
        ),
        migrations.AddField(
            model_name="license",
            name="choosealicense_permissions",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="license",
            name="choosealicense_conditions",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="license",
            name="choosealicense_limitations",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
