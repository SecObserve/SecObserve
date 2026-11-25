from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access_control", "0020_user_setting_hidden_observation_columns"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_service_account",
            field=models.BooleanField(default=False),
        ),
    ]
