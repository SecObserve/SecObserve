import logging
import traceback
from typing import Any

from django.core.management.base import BaseCommand

from application.licenses.models import License, License_Group, License_Policy
from application.licenses.services.license import import_licenses
from application.licenses.services.license_group import import_scancode_licensedb
from application.licenses.services.license_policy import create_scancode_standard_policy

logger = logging.getLogger("secobserve.licenses")


class Command(BaseCommand):

    help = "Initial load of licenses, license groups and license policies."

    def handle(self, *args: Any, **options: Any) -> None:
        licenses_exist = License.objects.exists()
        license_groups_exist = License_Group.objects.exists()
        license_policies_exist = License_Policy.objects.exists()

        if not licenses_exist and not license_groups_exist and not license_policies_exist:
            logger.info("Importing licenses, license groups and license policies ...")

            try:
                import_licenses()
                logger.info("... licenses imported from SPDX")

                import_scancode_licensedb()
                logger.info("... license groups imported from ScanCode LicenseDB")

                create_scancode_standard_policy()
                logger.info("... standard license policy created")
            except Exception as e:
                logger.error(str(e))
                logger.error(traceback.format_exc())
