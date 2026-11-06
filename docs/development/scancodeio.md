# ScanCode.io

## Starting the server

To have a close integration between SecObserve and [ScanCode.io](https://scancodeio.readthedocs.io), the script

```bash
./bin/scancodeio_dev.sh
```

starts both SecObserve and ScanCode.io in one Docker Compose environment. The ScanCode.io UI can then be accessed with [http://localhost:4100/](http://localhost:4100/).

SecObserve only supports ScanCode.io installations with activated authentication, so a user needs to be created in a shell of the `secobserve-scancodeio-1` container with:

```bash
./manage.py create-user --generate-api-key --admin --super admin
```

The API key of this user must be stored in the SecObserve settings for ScanCode.io.

The base URL of ScanCode.io in the SecObserve settings is `http://nginx`. The SecObserve backend runs in its own container, so `localhost` would not reach ScanCode.io. The host name `nginx` is allowed for ScanCode.io in `docker/scancodeio/.env`.

ScanCode.io notifies SecObserve with a webhook when a pipeline has finished. The SecObserve URL for ScanCode.io webhooks in the SecObserve settings is `http://backend:8000`. The webhook is registered when a project is created.

## Managing projects

ScanCode.io projects are managed in the `ScanCode.io` tab of a product. A product can have one project per combination of branch and service, both are optional. The name of a project must be unique in ScanCode.io and can have up to 100 characters. If no name is entered when creating a project, it is built from the names of the product, the branch and the service, and clipped to 100 characters. If the clipped name already exists, ScanCode.io rejects it and a name has to be entered.

A project is deleted together with its branch or service, also when the branch is deleted by the housekeeping. It is then deleted in ScanCode.io as well. A service cannot be deleted as long as it has license components.

## Importing the results

When a pipeline has finished successfully, SecObserve reads the packages and dependencies of the project from ScanCode.io in the background task `Import ScanCode.io results`, if license management is enabled:

* Every package becomes a license component of the product, with its name, version, purl, declared license and dependencies. The name includes the namespace (e.g. `@babel/core` or `org.apache.commons:commons-lang3`), except for operating system packages, whose namespace is the Linux distribution. ScanCode.io uses `pkg:alpine/...` for the purls of all apk packages. They are stored in their correct form with the distribution of the images as namespace (`pkg:apk/alpine/...`, `pkg:apk/wolfi/...` or `pkg:apk/chainguard/...`). If the images don't have one common distribution, `alpine` is used. The complete package data of ScanCode.io is stored as evidence, unchanged. The components belong to the branch and service of the project, and their filename is `ScanCode.io`. An import only changes the components of its own branch and service.
* If all analyzed Docker images have the same Linux distribution, it is stored with its release in the OSV settings of the project's branch, or of the product if the project has no branch. ScanCode.io's purls for operating system packages have no distro qualifier, so the OSV scan needs this setting to find their vulnerabilities. There are no OSV settings per service: If services of the same branch use different Linux distributions, the latest import wins, and the OSV scan can use the wrong distribution for the operating system packages of the other services.
* The last import date of the project's branch is updated, so the housekeeping doesn't treat the branch as inactive.

Vulnerabilities are not imported from ScanCode.io, they are found by the OSV and VulnerableCode scans of the license components.

The results can also be imported manually with `Re-import results` in the `ScanCode.io` tab of the product, e.g. after additional pipelines have been run in ScanCode.io. This import runs in the foreground and shows the numbers of new, updated and deleted license components when it has finished. Components that are no longer part of the results in ScanCode.io are deleted. If a pipeline is still running, its partial results are imported, and the import after its successful completion replaces them.


## Funding

<img src="https://nlnet.nl/logo/banner.svg" width="20%" alt="NLNet">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://nlnet.nl/image/logos/NGI0CommonsFund_tag.svg" width="20%" alt="NLNet">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[https://nlnet.nl/project/SecObservePlus](https://nlnet.nl/project/SecObservePlus)

Integration of SecObserve with [VulnerableCode](https://vulnerablecode.readthedocs.io) is funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund), a fund established by [NLnet](https://nlnet.nl/) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu/) programme, under the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en) under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429). Additional funding is made available by the [Swiss State Secretariat for Education, Research and Innovation](https://www.sbfi.admin.ch/sbfi/en/home.html) (SERI).
