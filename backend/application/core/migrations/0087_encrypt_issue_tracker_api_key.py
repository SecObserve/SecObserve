import encrypted_model_fields.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0086_observation_assessment_vex_remediations_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="issue_tracker_api_key",
            field=encrypted_model_fields.fields.EncryptedCharField(blank=True),
        ),
    ]
