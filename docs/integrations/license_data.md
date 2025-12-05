# License data import

## SPDX licenses

The [Linux Foundation](https://www.linuxfoundation.org/) gathers a list of commonly found licenses and exceptions used for open source and other collaborative software. The list is called [SPDX License List](https://spdx.org/licenses/) and is imported daily into SecObserve from a JSON file hosted on GitHub.

### Configuration

Per default the task to import the SPDX licenses is scheduled to run every night at 01:30 UTC time. This default can be changed by administrators via the [Settings](../getting_started/configuration.md#admininistration-in-secobserve). 

![SPDX license import configuration](../assets/images/screenshot_spdx_license_import.png){ width="80%" style="display: block; margin: 0 auto" }

Hour is always in UTC time.

##  ScanCode LicenseDB

The [ScanCode LicenseDB](https://scancode-licensedb.aboutcode.org) is a free and open database of mostly all the software licenses, including a category per license. License groups will be created with the initial startup of SecObserve for each category of the ScanCode License, containing the respective SPDX licenses, and updated every night after the update of the SPDX licenses.
