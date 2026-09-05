# Features

## Vulnerability Management

| Feature | Supported |
|---------|:------------:|
| [Flexible data model with products, product groups and services](../getting_started/data_model.md)  | :material-plus-circle-outline: |
| [Observations with a wide range of information](../getting_started/anatomy_of_an_observation.md) | :material-plus-circle-outline: |
| [Multiple branches and versions per product](../usage/branches.md) | :material-plus-circle-outline: |
| [Identified components with vulnerabilities and licenses across all products](../usage/components.md) | :material-plus-circle-outline: |
| [Automatic resolution of fixed vulnerabilities](../usage/import_observations.md#import-algorithm) | :material-plus-circle-outline: |
| [Identification and management of duplicates](../usage/duplicates.md) | :material-plus-circle-outline: |
| [Manual assessment of severity and status](../usage/assess_observations.md) | :material-plus-circle-outline: |
| [Rule based assessment of severity and status](../usage/rule_engine.md) | :material-plus-circle-outline: |
| [Security gates](../usage/security_gates.md) | :material-plus-circle-outline: |
| [Actual and weekly metrics](../usage/metrics.md) | :material-plus-circle-outline: |
| [Configurable expiry for accepted risks](../usage/risk_acceptance_expiry.md) | :material-plus-circle-outline: |

## License Management

| Feature | Supported |
|---------|:------------:|
| [Import of components with license information from CycloneDX and SPDX SBOMs](../usage/upload_sbom.md) | :material-plus-circle-outline: |
| [Flexible license policies to evaluate the impact of different license conditions](../usage/license_management.md#managing-license-policies) | :material-plus-circle-outline: |
| [Organize licenses with similar conditions in license groups](../usage/license_management.md#managing-license-groups) | :material-plus-circle-outline: |

## Integrations

| Feature | Supported |
|---------|:------------:|
| [Import from many SAST, SCA, DAST, infrastructure and secrets scanners](../integrations/supported_scanners.md) | :material-plus-circle-outline: |
| [GitLab CI integration of scanners with predefined templates](../integrations/github_actions_and_templates.md#examplary-pipeline-for-gitlab-ci-templates)<br />[GitHub integration of scanners with predefined actions](../integrations/github_actions_and_templates.md#examplary-workflow-for-github-actions) | :material-plus-circle-outline: |
| [Data enrichment from Exploit Prediction Scoring System (EPSS)](../integrations/epss.md) | :material-plus-circle-outline: |
| [Data enrichment with exploit information](../integrations/exploit_information.md) | :material-plus-circle-outline: |
| [Always up-to-date SPDX licenses](../integrations/license_data.md#spdx-licenses) | :material-plus-circle-outline: |
| [License groups generated from ScanCode LicenseDB data](../integrations/license_data.md#scancode-licensedb) | :material-plus-circle-outline: |
| [Direct link to source code](../integrations/source_code_repositories.md) | :material-plus-circle-outline: |
| [Export vulnerabilities to issue trackers (Jira, GitLab, GitHub)](../integrations/issue_trackers.md) | :material-plus-circle-outline: |
| [Import/export vulnerabilities from/to VEX documents (CSAF, OpenVEX)](../integrations/vex.md) | :material-plus-circle-outline: |
| [Vulnerability scanning from OSV](../integrations/osv_scan.md) | :material-plus-circle-outline: |
| [Vulnerability scanning from VulnerableCode](../integrations/vulnerablecode_scan.md) | :material-plus-circle-outline: |
| [Export of data to Microsoft Excel and CSV](../integrations/observations_export.md) | :material-plus-circle-outline: |
| [Export metrics to CodeCharta](../integrations/codecharta.md) | :material-plus-circle-outline: |
| [Notifications to Microsoft Teams, Slack and email](../integrations/notifications.md) | :material-plus-circle-outline: |
| [Links to additional information about vulnerabilities and components](../integrations/links.md) | :material-plus-circle-outline: |
| [REST API](../integrations/rest_api.md) | :material-plus-circle-outline: |

## Access Control

| Feature | Supported |
|---------|:------------:|
| [Built-in user management](../usage/users_permissions.md#users) | :material-plus-circle-outline: |
| [OpenID Connect integration](../integrations/oidc_authentication.md) | :material-plus-circle-outline: |
| [Internal, external and admin users](../usage/users_permissions.md#user-types) | :material-plus-circle-outline: |
| [Authorization groups](../usage/users_permissions.md#authorization-groups) | :material-plus-circle-outline: |
| [Role-based access control](../usage/users_permissions.md#roles-and-permissions) | :material-plus-circle-outline: |

## Installation and Upgrading

| Feature | Supported |
|---------|:------------:|
| [Installation with Docker Compose](../getting_started/installation.md) | :material-plus-circle-outline: |
| [Supported databases: PostgreSQL and MySQL](../getting_started/architecture.md) | :material-plus-circle-outline: |
| [Flexible configuration](../getting_started/configuration.md) | :material-plus-circle-outline: |
| [Automatic database migration during upgrades](../getting_started/upgrading.md) | :material-plus-circle-outline: |
