from json import loads

import requests

from application.licenses.models import License, License_Group, License_Group_Member


def copy_license_group(source_license_group: License_Group, name: str) -> License_Group:
    new_license_group = License_Group.objects.create(
        name=name, description=source_license_group.description, is_public=source_license_group.is_public
    )

    for license_to_be_added in source_license_group.licenses.all():
        new_license_group.licenses.add(license_to_be_added)

    members = License_Group_Member.objects.filter(license_group=source_license_group)
    for member in members:
        License_Group_Member.objects.update_or_create(
            license_group=new_license_group, user=member.user, is_manager=member.is_manager
        )

    return new_license_group


def import_scancode_licensedb() -> None:
    license_groups: dict[str, License_Group] = {}

    response = requests.get("https://scancode-licensedb.aboutcode.org/index.json", timeout=60, stream=True)
    response.raise_for_status()
    data = loads(response.content)

    for db_license in data:
        category = db_license.get("category")
        spdx_license_key = db_license.get("spdx_license_key")
        other_spdx_license_keys = db_license.get("other_spdx_license_keys", [])

        if category and spdx_license_key:
            _add_license_to_group(license_groups, category, spdx_license_key)
            for other_spdx_license_key in other_spdx_license_keys:
                _add_license_to_group(license_groups, category, other_spdx_license_key)


def _add_license_to_group(license_groups: dict[str, License_Group], category: str, spdx_license_key: str) -> None:
    try:
        spdx_license = License.objects.get(spdx_id=spdx_license_key)
        license_group = license_groups.get(category)
        if not license_group:
            license_group, _ = License_Group.objects.get_or_create(
                name=f"{category} (ScanCode LicenseDB)",
                defaults={
                    "description": "**Do not edit!** "
                    + "Imported from [ScanCode LicenseDB](https://scancode-licensedb.aboutcode.org/) "
                    + "under the CC-BY-4.0 license and updated every 24 hours.",
                    "is_public": True,
                },
            )
            license_groups[category] = license_group
            license_group.licenses.clear()
        license_group.licenses.add(spdx_license)
    except License.DoesNotExist:
        pass
