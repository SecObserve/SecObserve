from django.apps import AppConfig


class AuditTrailConfig(AppConfig):
    name = "application.audit_trail"
    verbose_name = "Audit Trail"

    def ready(self) -> None:
        from application.audit_trail.signals import (  # pylint: disable=import-outside-toplevel
            connect_signals,
        )

        connect_signals()
