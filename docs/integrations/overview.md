# Overview

![Integrations](../assets/images/secobserve_integrations.svg)

<div class="grid cards" markdown>

-   :fontawesome-brands-openid:{ .lg .middle } __Authentication__

    ---

    All `OpenID Connect` providers are supported for authentication with an external user directory.

    [:octicons-arrow-right-24: OpenID Connect](oidc_authentication.md)

-   :material-puzzle:{ .lg .middle } __Components__

    ---

    Components can be uploaded from CycloneDX and SPDX SBOMs for vulnerability scanning and license management.

    [:octicons-arrow-right-24: Upload SBOM](../usage/upload_sbom.md)

-   :material-magnify:{ .lg .middle } __Vulnerabilities__

    ---

    Vulnerability data can be imported from the results of several vulnerability scanners. Additionally components
    can be scanned by SecObserve against OSV or VulnerableCode.

    [:octicons-arrow-right-24: Supported scanners](supported_scanners.md)

    [:octicons-arrow-right-24: OSV scan](osv_scan.md)

    [:octicons-arrow-right-24: VulnerableCode scan](vulnerablecode_scan.md)

-   :material-skull-scan:{ .lg .middle } __EPSS Scores, Exploits__

    ---

    Observations with a CVE Id are enriched with EPSS scores and information about exploits. The necessary data is
    imported automatically every night.
    
    [:octicons-arrow-right-24: EPSS scores](epss.md)

    [:octicons-arrow-right-24: Exploit information](exploit_information.md)

-   :material-license:{ .lg .middle } __Licences, License Groups__

    ---

    The list of SPDX licenses is updated nightly. Additionally superusers can manually import license groups generated
    from the ScanCode LicenseDB.

    [:octicons-arrow-right-24: License data](license_data.md)

-   :material-security:{ .lg .middle } __VEX Import/Export__

    ---

    Vulnerability Exploitability eXchange (VEX) documents can be imported and exported in CSAF, CycloneDX and OpenVEX
    format.

    [:octicons-arrow-right-24: VEX documents](vex.md)

-   :material-download:{ .lg .middle } __Observation and License Export__

    ---

    Observations and licenses of a product or product group can be exported to CSV or MS Excel files.

    [:octicons-arrow-right-24: Export of observations](observations_export.md)

-   :material-exclamation-thick:{ .lg .middle } __Issues__

    ---

    SecObserve supports automatic creation of issues in GitHub, GitLab and Jira (Cloud).

    [:octicons-arrow-right-24: Issue trackers](issue_trackers.md)

-   :material-open-in-new:{ .lg .middle } __Code links__

    ---

    For observations originating from a source file, a link can be generated to view it in the
    source code repository.

    [:octicons-arrow-right-24: Source code repositories](source_code_repositories.md)

-   :material-bell-ring:{ .lg .middle } __Notifications__

    ---

    SecObserve can send notifications via email, MS Teams or Slack when a security gate changes
    or an exception occurs.

    [:octicons-arrow-right-24: Notifications](notifications.md)

-   :material-open-in-new:{ .lg .middle } __Information links__

    ---

    Observations and components show links to get further information from external sources.

    [:octicons-arrow-right-24: Links to additional information](links.md)

-   :material-cog:{ .lg .middle } __REST API__

    ---

    SecObserve is build with an API first approach, every functionality needed to use SecObserve 
    is covered by the REST API.

    [:octicons-arrow-right-24: REST API](rest_api.md)

</div>
