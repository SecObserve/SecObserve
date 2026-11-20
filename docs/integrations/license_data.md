# License data import

## SPDX licenses

The [Linux Foundation](https://www.linuxfoundation.org/) gathers a list of commonly found licenses and exceptions used for open source and other collaborative software. The list is called [SPDX License List](https://spdx.org/licenses/) and is imported daily into SecObserve from a JSON file hosted on GitHub.

### Configuration

Per default the task to import the SPDX licenses is scheduled to run every night at 01:30 UTC time. This default can be changed by administrators via the [Settings](../getting_started/configuration.md#administration-in-secobserve). 

![SPDX license import configuration](../assets/images/screenshot_spdx_license_import.png){ width="80%" style="display: block; margin: 0 auto" }

Hour is in UTC, unless [`TIME_ZONE`](../getting_started/configuration.md#time-zone-of-the-background-tasks) is set.

## ScanCode LicenseDB

The [ScanCode LicenseDB](https://scancode-licensedb.aboutcode.org) is a free and open database of mostly all the software licenses, including a category per license. License groups will be created with the initial startup of SecObserve for each category of the ScanCode License, containing the respective SPDX licenses, and updated every night after the update of the SPDX licenses.

Additionally, each SPDX license is enriched every Sunday (UTC) with data from the ScanCode LicenseDB: category, owner, homepage, and URLs of the license text and FAQ. They are shown in a section of their own on the license page, and the category can be used to filter and sort lists of licenses. A license is matched by its SPDX id against the SPDX license key of a ScanCode license, or against one of its other SPDX license keys, e.g. a deprecated SPDX id.

## choosealicense.com

[choosealicense.com](https://choosealicense.com) by GitHub summarizes common open source licenses in plain language: a short description and the permissions, conditions and limitations of each license, e.g. *Commercial use*, *Disclose source* or *Liability*.

This summary is imported every Sunday (UTC) after the update of the SPDX licenses and shown on the license page in a section of its own. A license is matched by its SPDX id. choosealicense.com uses some deprecated SPDX ids, e.g. `GPL-3.0`, their data is also used for the respective `-only` and `-or-later` licenses, e.g. `GPL-3.0-only` and `GPL-3.0-or-later`. The content of choosealicense.com is licensed under the CC-BY-3.0 license.

## LicenseLynx

[LicenseLynx](https://licenselynx.org/) is a project focused on deterministically map unknown or ambiguous license names and their canonical license names. Imported license names which are not SPDX licenses will be mapped with LicenseLynx to find the correct SPDX license if possible.
