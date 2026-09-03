import django.db.models.deletion
from django.db import migrations, models

# Until now Component was an unmanaged model backed by the database view "core_component",
# which was created on demand before the first query (see migration 0077). The view has to be
# dropped before the table of the same name can be created.
DROP_COMPONENT_VIEW = "DROP VIEW IF EXISTS core_component;"


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0097_product_automatic_vulnerablecode_scanning_enabled_and_more"),
    ]

    operations = [
        # The old model is unmanaged, so this only removes it from the migration state.
        migrations.DeleteModel(
            name="Component",
        ),
        migrations.RunSQL(
            sql=DROP_COMPONENT_VIEW,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.CreateModel(
            name="Component",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identity_hash", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("version", models.CharField(blank=True, max_length=255)),
                ("name_version", models.CharField(blank=True, max_length=513)),
                ("type", models.CharField(blank=True, max_length=24)),
                ("purl", models.CharField(blank=True, max_length=255)),
                ("purl_type", models.CharField(blank=True, max_length=16)),
                ("purl_namespace", models.CharField(blank=True, max_length=255)),
                ("cpe", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.AddIndex(
            model_name="component",
            index=models.Index(fields=["name_version"], name="core_compon_name_ve_2106e0_idx"),
        ),
        migrations.AddIndex(
            model_name="component",
            index=models.Index(fields=["purl"], name="core_compon_purl_247d52_idx"),
        ),
        migrations.AddField(
            model_name="observation",
            name="origin_component",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="core.component"),
        ),
    ]
