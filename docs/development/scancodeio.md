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

## Importing the results

When a pipeline has finished successfully, SecObserve reads the packages and dependencies of the project from ScanCode.io in the background task `Import ScanCode.io results`, if license management is enabled:

* Every package becomes a license component of the product, with its name, version, purl, declared license and dependencies. The complete package data of ScanCode.io is stored as evidence. The components belong to neither a branch nor a service, and their filename is `ScanCode.io`.
* If all analyzed Docker images have the same Linux distribution, it is stored with its release in the OSV settings of the product. ScanCode.io's purls for operating system packages have no distro qualifier, so the OSV scan needs this setting to find their vulnerabilities.

Vulnerabilities are not imported from ScanCode.io, they are found by the OSV and VulnerableCode scans of the license components.


## Funding

<img src="https://nlnet.nl/logo/banner.svg" width="20%" alt="NLNet">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://nlnet.nl/image/logos/NGI0CommonsFund_tag.svg" width="20%" alt="NLNet">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[https://nlnet.nl/project/SecObservePlus](https://nlnet.nl/project/SecObservePlus)

Integration of SecObserve with [VulnerableCode](https://vulnerablecode.readthedocs.io) is funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund), a fund established by [NLnet](https://nlnet.nl/) with financial support from the European Commission's [Next Generation Internet](https://ngi.eu/) programme, under the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en) under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429). Additional funding is made available by the [Swiss State Secretariat for Education, Research and Innovation](https://www.sbfi.admin.ch/sbfi/en/home.html) (SERI).
