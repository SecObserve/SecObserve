from decimal import Decimal
from typing import Optional

from django.utils import timezone

from application.core.models import Branch, Observation, Product
from application.core.types import Severity, Status


class ObservationFixtureMixin:
    """Saves product_1 with branch_1 as default branch and creates observations on them."""

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        # BaseTestCase links the unsaved branch already, which blocks the first save;
        # saving the branch as default branch links it back through the branch signal.
        self.product_1.repository_default_branch = None
        self.product_1.save()
        self.branch_1.is_default_branch = True
        self.branch_1.save()
        self.parser_1.save()

    def _observation(  # pylint: disable=too-many-arguments
        self,
        title: str,
        *,
        vulnerability_id: str = "CVE-2026-1",
        severity: str = Severity.SEVERITY_CRITICAL,
        status: str = Status.STATUS_OPEN,
        cve_found_in: str = "",
        epss: Optional[Decimal] = None,
        cvss3_vector: str = "",
        cvss4_vector: str = "",
        fix_available: Optional[bool] = None,
        branch: Optional[Branch] = None,
        product: Optional[Product] = None,
    ) -> Observation:
        # fix_available is derived from the recommendation on save, so a component and a
        # recommendation with a version are the only way to get True.
        component = {}
        if fix_available is not None:
            component = {
                "origin_component_name": "component",
                "origin_component_version": "1.0.0",
                "recommendation": "Upgrade to 1.0.1" if fix_available else "",
            }
        return Observation.objects.create(
            product=product or self.product_1,
            branch=branch or self.branch_1,
            parser=self.parser_1,
            import_last_seen=timezone.now(),
            title=title,
            vulnerability_id=vulnerability_id,
            parser_severity=severity,
            current_severity=severity,
            parser_status=status,
            current_status=status,
            cve_found_in=cve_found_in,
            epss_score=epss,
            cvss3_vector=cvss3_vector,
            cvss4_vector=cvss4_vector,
            **component,
        )
