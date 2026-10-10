from io import StringIO
from unittest.mock import patch

from defusedcsv import csv
from django.http import HttpResponse

from application.commons.models import Settings
from application.core.models import Component
from application.core.queries.component import get_components
from application.core.services.export_components import (
    COLUMNS,
    export_components_csv,
)
from unittests.base_test_case import BaseTestCase


class TestExportComponents(BaseTestCase):
    @patch("application.core.queries.component.get_current_user")
    def test_export_components_csv(self, mock_user):
        mock_user.return_value = self.user_admin
        settings = Settings.load()
        settings.base_url_frontend = "https://secobserve.example.com"
        settings.save()
        component = Component.objects.create(
            identity_hash="export_components",
            name="snakeyaml",
            version="2.2",
            name_version="snakeyaml:2.2",
            type="Library",
            purl="pkg:maven/org.yaml/snakeyaml@2.2",
            purl_type="maven",
            purl_namespace="org.yaml",
        )

        response = HttpResponse()
        export_components_csv(response, get_components().filter(pk=component.pk))

        rows = list(csv.reader(StringIO(response.content.decode())))
        self.assertEqual([column.header for column in COLUMNS], rows[0])
        self.assertEqual(
            {
                "Active observations": "False",
                "Component URL": f"https://secobserve.example.com/#/components/{component.pk}/show",
                "Ecosystem": "maven",
                "Inactive observations": "False",
                "Licenses": "False",
                "Name": "snakeyaml",
                "Namespace": "org.yaml",
                "PURL": "pkg:maven/org.yaml/snakeyaml@2.2",
                "Type": "Library",
                "Version": "2.2",
            },
            dict(zip(rows[0], rows[1])),
        )
        self.assertEqual(2, len(rows))
