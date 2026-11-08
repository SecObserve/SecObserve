# ScanCode.io (experimental)

!!! warning
    The integration with ScanCode.io is **experimental**. It is not yet feature complete and the results might not be as accurate as expected.

[ScanCode.io](https://scancodeio.readthedocs.io) analyzes codebases, Docker images, package archives and manifests in scripted pipelines to identify packages, their dependencies and their licenses. SecObserve creates projects in ScanCode.io, lets them run a pipeline and gets notified by ScanCode.io when the pipeline has finished. The packages found by ScanCode.io are then imported as license components of the product.

There are 4 preconditions to be met before ScanCode.io can be used:

* License management has to be enabled in the `Features` section of the [Settings](../getting_started/configuration.md#administration-in-secobserve).
* The ScanCode.io integration has to be enabled and configured in the [Settings](#configuration-in-settings).
* SecObserve only supports ScanCode.io installations with activated authentication.
* Only superusers and users with the role `Maintainer` or `Owner` for a product can manage its ScanCode.io projects.

## Configuration in Settings

The ScanCode.io parameters are configured in the `Features` section of the [Settings](../getting_started/configuration.md#administration-in-secobserve).

- **Enable ScanCode.io integration**
- **ScanCode.io base URL:** The URL of the ScanCode.io instance without a trailing path, as reached by the SecObserve backend. SecObserve doesn't follow redirects from ScanCode.io, so this has to be the final URL, e.g. with `https` if the instance redirects `http` to `https`.
- **ScanCode.io API key:** The API key of a ScanCode.io user. A user with an API key can be created in a shell of the ScanCode.io container with:

    ```bash
    ./manage.py create-user --generate-api-key <username>
    ```

- **SecObserve URL for ScanCode.io webhooks:** ScanCode.io notifies SecObserve with a webhook when a pipeline has finished. This is the base URL of SecObserve as reached by ScanCode.io, e.g. `https://secobserve-backend.example.com`. The webhook is registered when a project is created. ScanCode.io sends webhooks without authentication, so the webhook URL of each project contains a secret token.

## Managing projects

ScanCode.io projects are managed in the `ScanCode.io` tab of a product. A product can have one project per combination of branch and service, both are optional.

A project is created with `Create ScanCode.io project`:

- **Branch / Version:** Optional, the default is the repository default branch of the product.
- **Service:** Optional, only shown if the product has services.
- **Project name:** The name of a project must be unique in ScanCode.io and can have up to 100 characters. If no name is entered, it is built from the names of the product, the branch and the service, and clipped to 100 characters. If the clipped name already exists, ScanCode.io rejects it and a name has to be entered.
- **Input URLs:** URLs of the inputs to be analyzed, e.g. `http(s)://` download URLs, `docker://` references of Docker images, Git repositories ending with `.git` or package URLs starting with `pkg:`.
- **File to upload:** A file to be analyzed, e.g. an archive or a manifest. At least one input URL or a file to upload is required.
- **Pipeline:** The ScanCode.io pipeline to be run. Add-on pipelines cannot be used to create a project.
- **Execute pipeline now:** If not set, the pipeline has to be started in ScanCode.io.

`Show` displays the details of a project as they are stored in ScanCode.io: its inputs, the numbers of resources, packages, dependencies, relations and messages, and its pipeline runs. The name of the project links to the project in the ScanCode.io UI, where additional pipelines can be run.

`Delete` deletes the project in SecObserve and in ScanCode.io, after its name has been entered as confirmation. A project is also deleted together with its branch or service, also when the branch is deleted by the [housekeeping](../usage/branches.md#housekeeping). It is then deleted in ScanCode.io as well. A service cannot be deleted as long as it has license components.

## Importing the results

When a pipeline has finished successfully, SecObserve reads the packages and dependencies of the project from ScanCode.io in the background task `Import ScanCode.io results`:

* Every package becomes a license component of the product, with its name, version, purl, declared license and dependencies.The complete package data of ScanCode.io is stored as evidence, unchanged. The components belong to the branch and service of the project, and their filename is `ScanCode.io`.
* If all analyzed Docker images have the same Linux distribution, it is stored with its release in the [OSV settings](./osv_scan.md#vulnerability-scanning-from-osv) of the project's branch, or of the product if the project has no branch. ScanCode.io's purls for operating system packages have no distro qualifier, so the OSV scan needs this setting to find their vulnerabilities. 
* The last import date of the project's branch is updated, so the housekeeping doesn't treat the branch as inactive.

Vulnerabilities are not imported from ScanCode.io, they are found by the [OSV](./osv_scan.md) and [VulnerableCode](./vulnerablecode_scan.md) scans of the license components.

The results can also be imported manually with `Re-import results` in the `ScanCode.io` tab of the product, e.g. after additional pipelines have been run in ScanCode.io. This import runs in the foreground and shows the numbers of new, updated and deleted license components when it has finished. Components that are no longer part of the results in ScanCode.io are deleted. If a pipeline is still running, its partial results are imported, and the import after its successful completion replaces them.


## Funding

<img src="https://nlnet.nl/logo/banner.svg" width="20%" alt="NLNet">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://nlnet.nl/image/logos/NGI0CommonsFund_tag.svg" width="20%" alt="NGI0 Commons Fund">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[https://nlnet.nl/project/SecObservePlus](https://nlnet.nl/project/SecObservePlus)

Integration of SecObserve with [ScanCode.io](https://scancodeio.readthedocs.io) is funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund), a fund established by [NLnet](https://nlnet.nl/) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu/) programme, under the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en) under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429). Additional funding is made available by the [Swiss State Secretariat for Education, Research and Innovation](https://www.sbfi.admin.ch/sbfi/en/home.html) (SERI).
