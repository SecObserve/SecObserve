from typing import Optional

from application.licenses.models import License
from application.licenses.queries.license import get_license_by_spdx_id


class SPDXLicenseCache:

    NO_ENTRY = "no_entry"

    def __init__(self) -> None:
        self.cache: dict[str, License | str] = {}

    def get(self, spdx_id: str) -> Optional[License]:
        if " or " in spdx_id.lower() or " and " in spdx_id.lower():
            # This is a license expression
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
