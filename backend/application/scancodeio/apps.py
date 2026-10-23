from django.apps import AppConfig


class ScanCodeIOConfig(AppConfig):
    name = "application.scancodeio"
    verbose_name = "ScanCode.io"

    def ready(self) -> None:
        import config.schema  # noqa: F401 pylint: disable=import-outside-toplevel, unused-import
