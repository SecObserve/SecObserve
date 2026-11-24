from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access_control", "0021_user_is_service_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="instance_role",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
