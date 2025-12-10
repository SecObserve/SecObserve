import re
from typing import Optional

from application.licenses.models import License
from application.licenses.queries.license import get_license_by_spdx_id

SPDX_ID_REGEX = re.compile("^[A-Za-z0-9-.+:]+$")


class SPDXLicenseCache:

    NO_ENTRY = "no_entry"

    def __init__(self) -> None:
        self.cache: dict[str, License | str] = {}

    def get(self, spdx_id: str) -> Optional[License]:
        if not SPDX_ID_REGEX.match(spdx_id):
            return None

        spdx_license = self.cache.get(spdx_id)
        if spdx_license:
            if isinstance(spdx_license, License):
                return spdx_license
            return None

        spdx_license = get_license_by_spdx_id(spdx_id)
        if spdx_license:
            self.cache[spdx_id] = spdx_license
            return spdx_license

        self.cache[spdx_id] = SPDXLicenseCache.NO_ENTRY
        return None
