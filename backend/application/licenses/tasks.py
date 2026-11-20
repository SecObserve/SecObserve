from huey.contrib.djhuey import db_task

from application.licenses.services.license_choosealicense import import_choosealicense
from application.licenses.services.license_group import import_scancode_licensedb
from application.notifications.services.tasks import handle_task_exception


@db_task()
def task_import_license_details() -> None:
    """Downloading the details of all licenses takes several minutes, so it must not block the startup"""
    try:
        import_scancode_licensedb()
        import_choosealicense()
    except Exception as e:
        handle_task_exception(e)
        raise
