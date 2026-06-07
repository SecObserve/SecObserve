from django.core.paginator import Paginator
from django.db import migrations


def reencrypt_issue_tracker_api_key(apps, schema_editor):
    from encrypted_model_fields.fields import EncryptedCharField

    field = EncryptedCharField()
    connection = schema_editor.connection

    Product = apps.get_model("core", "Product")
    ids = list(Product.objects.exclude(issue_tracker_api_key="").order_by("id").values_list("id", flat=True))
    paginator = Paginator(ids, 1000)
    for page_number in paginator.page_range:
        page_ids = list(paginator.page(page_number).object_list)

        rows = Product.objects.filter(id__in=page_ids).order_by("id").values_list("id", "issue_tracker_api_key")
        with connection.cursor() as cursor:
            for pk, plaintext in rows:
                encrypted = field.get_db_prep_save(plaintext, connection=connection)
                cursor.execute(
                    "UPDATE core_product SET issue_tracker_api_key = %s WHERE id = %s",
                    [encrypted, pk],
                )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0087_encrypt_issue_tracker_api_key"),
    ]

    operations = [
        migrations.RunPython(
            reencrypt_issue_tracker_api_key,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
