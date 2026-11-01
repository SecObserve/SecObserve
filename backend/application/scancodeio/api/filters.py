from django_filters import FilterSet

from application.scancodeio.models import ScanCodeIO_Project


class ScanCodeIOProjectFilter(FilterSet):
    class Meta:
        model = ScanCodeIO_Project
        fields = ["product"]
