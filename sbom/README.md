# Software Bill of Materials (SBOM)

The CycloneDX SBOMs of SecObserve are not stored in this repository. They are generated for each release (starting with release 1.64.0) by the job `generate_sboms` of the GitHub workflow [build_push_release.yml](../.github/workflows/build_push_release.yml) and published in two places:

* **Container images:** The [backend image](https://github.com/SecObserve/SecObserve/pkgs/container/secobserve-backend) and the [frontend image](https://github.com/SecObserve/SecObserve/pkgs/container/secobserve-frontend) each have their SBOM attached as an attestation, signed with [cosign](https://github.com/sigstore/cosign).
* **GitHub release:** The image SBOMs and the combined SBOM are attached as assets to the [GitHub release](https://github.com/SecObserve/SecObserve/releases).

This directory only contains the configuration to generate the SBOMs.

The published SBOMs are:

* `sbom_backend_RELEASE.json` - SBOM of the backend application and container, attached to the backend image
* `sbom_frontend_RELEASE.json` - SBOM of the frontend application and container, attached to the frontend image
* `sbom_RELEASE.json` - Combined SBOM of the backend and frontend applications and containers

They are merged from 4 intermediate SBOMs, which are not published:

* `sbom_backend_application_RELEASE.json` - Python libraries of the backend application, derived from [../backend/poetry.lock](../backend/poetry.lock)
* `sbom_frontend_application_RELEASE.json` - NPM libraries of the frontend application, derived from [../frontend/package-lock.json](../frontend/package-lock.json)
* `sbom_backend_container_RELEASE.json` - Operating system components of the backend container, derived from the backend image of the release
* `sbom_frontend_container_RELEASE.json` - Operating system components of the frontend container, derived from the frontend image of the release


## Verify and download the SBOM of an image

The attestations are signed keyless with the identity of the GitHub workflow. This command verifies the signature and extracts the SBOM of the backend image:

```bash
cosign verify-attestation --type cyclonedx \
  --certificate-identity-regexp '^https://github.com/SecObserve/SecObserve/\.github/workflows/build_push_release\.yml@' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/secobserve/secobserve-backend:RELEASE \
  | jq -r '.payload' | base64 -d | jq '.predicate' > sbom_backend_RELEASE.json
```

For the frontend image, replace `secobserve-backend` with `secobserve-frontend`.


## Verify the signature and build provenance of an image

Starting with release 1.64.0, the images are signed with [cosign](https://github.com/sigstore/cosign) and have a signed [SLSA build provenance](https://slsa.dev/spec/v1.0/provenance) attestation, which states the repository, commit, workflow and run that built the image. Both are created keyless with the identity of the GitHub workflow.

Verify the signature of the backend image:

```bash
cosign verify \
  --certificate-identity-regexp '^https://github.com/SecObserve/SecObserve/\.github/workflows/build_push_release\.yml@' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/secobserve/secobserve-backend:RELEASE
```

Verify the build provenance of the backend image with the [GitHub CLI](https://cli.github.com/manual/gh_attestation_verify):

```bash
gh attestation verify oci://ghcr.io/secobserve/secobserve-backend:RELEASE \
  --repo SecObserve/SecObserve \
  --signer-workflow SecObserve/SecObserve/.github/workflows/build_push_release.yml
```

For the frontend image, replace `secobserve-backend` with `secobserve-frontend`.


## Minimum requirements for content

* `metadata/component` 
    * name
    * version
    * description
    * supplier
    * purl
    * license (for application SBOMs)
* `components`
    * name
    * version
    * purl
    * licenses
    * type
* `dependencies`
    * hierarchical dependencies, starting from the `metadata/component`


## Design decisions

* **Split into 4 SBOMs**
    * Backend and frontend could be installed separately
    * Backend and frontend could be installed without using the docker images
    * Backend container does not contain hierarchy of Python libraries
    * Frontend container does not contain identifiable NPM libraries, because of the `vite` build process
* **Merge into one SBOM per image**
    * Users of an image get the components of the application and the container from one source
* **Signed attestation on the multi-platform image**
    * The SBOM is attached to the image index, which is what the release tag points to
    * The operating system components are taken from the `linux/amd64` image, the `linux/arm64` image contains the same packages for a different architecture
* **Signature and build provenance on the multi-platform image**
    * Like the SBOM, both are attached to the image index
    * The build provenance is created with [actions/attest](https://github.com/actions/attest) and stored in the container registry and in the GitHub attestations of the repository
* **Merge into combined SBOM**
    * For a complete overview of the applications and containers
* **Automated generation by GitHub workflow [build_push_release.yml](../.github/workflows/build_push_release.yml)**
    * Tracebility of SBOM content to the source files
