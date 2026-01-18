# Upgrading

## Generic upgrade procedure

* Frontend and backend shall always be started with the same version number. 

* The Docker Compose `docker-compose-prod-mysql.yml` and `docker-compose-prod-postgres.yml` in the GitHub repository always use the most recent released version of SecObserve.

* The database structure will automatically be updated to the reflect the latest changes, when the backend container gets started. **Always make a backup of your database before upgrading, in case something should go wrong.**

* There will be specific upgrade instructions if necessary, e.g. when there are new configuration parameters.

## Release 1.47.0

**Breaking changes**

* The OIDC attribute `prompt` is now configurable and it is not set as default. To return to the former behaviour, you have to set the environment variable `OIDC_PROMPT=select_account` for the frontend in your installation. For further details search for `prompt` in the [OpenID specification](https://openid.net/specs/openid-connect-core-1_0.html).


## Release 1.46.0

**Breaking changes**

* The results of API list endpoints for `products/`, `license_components/`, `licences/`, `license_groups/` and `license_policies/` contained some attributes that were used to streamline the user interface for single instances but are not necessary for list views and needed a lot of interactions with the database. These attributes have been removed from the result sets for performance optimization.


## Release 1.42.0

!!! warning
    The database migration in version 1.42.0 did not work on some installations with MySQL databases and aborted with an error message. MySQL users should skip this version and update directly to 1.43.0.


**Breaking changes**

!!! info
    The location of the Docker images has been changed with release 1.42.0, they are now stored in a GitHub container registry:

    * **ghcr.io/secobserve/secobserve-backend**
    * **ghcr.io/secobserve/secobserve-frontend**

    Please adjust your pull statements accordingly.


## Release 1.40.0

**Breaking changes**

* The field `[origin_]component_purl_namespace` has been removed from the APIs for `observations`, `license_components` and `components`. Users of the API shall parse the `[origin_]component_purl` if they need any of its attributes.

## Release 1.38.0

**Noteable change**

* Microsoft is rotating the root certificate for the flexible Azure Database for MySQL see [https://learn.microsoft.com/en-us/azure/mysql/flexible-server/concepts-root-certificate-rotation](https://learn.microsoft.com/en-us/azure/mysql/flexible-server/concepts-root-certificate-rotation). This release contains the new certificates.

## Release 1.37.0

**Breaking changes**

* The API for `license_components` has been changed, due to the rename of the existing license fields to `imported_declared_license_...` in [https://github.com/SecObserve/SecObserve/pull/3229](https://github.com/SecObserve/SecObserve/pull/3229).

## Release 1.30.0

**Noteable change**

* If multiple licenses have been found for a component, they are now evaluated like an `AND` expression. If for example one license is `Allowed` and the other one is `Forbidden`, the component is evaluated as `Forbidden`. An explicit rule in a License Policy is not necessary anymore. This new behaviour comes into effect with the next import of components.
* There is now an explicit menu in the UI and an API endpoint to import SBOMs to get all components with their licenses and dependencies, see [Upload SBOMs](../usage/upload_sbom.md).

## Release 1.26.0

**Breaking changes**

* The attribute `unknown_license` in License Components and License Policies has been renamed to `non_spdx_license`. This was necessary to avoid confusion with the License Policy evaluation result `Unknown`, when a license is not included in the License Policy.
* Additionally the attributes `name`, `version`, `name_version`, `dependencies`, `purl`, `purl_type` and `cpe` in License Components have been renamed to `component_name`, `component_version`, `component_name_version`, `component_dependencies`, `component_purl`, `component_purl_type` and `component_cpe` respectively. This brings it more in line with the component information in Observations.

**Noteable change**

* The parser does not need to specified anymore when importing observations from files via the API or the UI. The parser is detected automatically by the content of the imported file. If the parser is still in the attributes of the API call, it will be ignored.

## Release 1.22.0

**Breaking changes**

* Due to a library change, the `OCSF (Open Cybersecurity Schema Framework)` parser now only supports reports from Prowler 4.5.0 and above.


## Release 1.21.0

**Breaking changes**

* There was a typo in severities, where there was a missing "n" in "Unknown". This has been fixed in the code as well as in the data. If you use the severity "Unknown" in API calls, you need to change it from "Unkown" to "Unknown".


## Release 1.18.0

**Breaking changes**

* The `Prowler` parser has been renamed to `Prowler 3`, because it supports only Prowler up to version 3. For Prowler version 4 and above use the `OCSF (Open Cybersecurity Schema Framework)` parser.
* Component dependencies are now shown as a diagram. To do this, the format of the dependencies in the database had to be changed. The migration to the new format is not completely lossless and might loose some information. With the next import of observations, the dependencies will be complete again.

## Release 1.5.0

**Breaking changes**

* The tag of the docker image is not part of the identity hash anymore, to allow updates of the docker image within a vulnerability check without creating a new observation.

## Release 1.3.0

**Breaking changes**

* The [ZAP project](https://www.zaproxy.org) has had a rebranding as a result of the move to the Software Security Project. To reflect this, the name of the parser has been changed from `OWASP ZAP` to `ZAP`. The GitLab template and GitLab action for `ZAP` have been renamed as well. These changes are not backwards compatible, so you need to update your configuration files and pipelines.

## Release 1.1.0

**Breaking changes**

* When OIDC authentication is used, the environment variable `OIDC_CLIENT_ID` needs to be set for the backend as well. See [Configuration](configuration.md) and [OpenID Connect authentication](../integrations/oidc_authentication.md) for details.

## Release 1.0.0

**Breaking changes**

* SecObserve now supports different OpenID Connect providers for authentication and the Microsoft specific dependencies have been removed. Thus the `AAD_` configuration parameters are not valid anymore and have been replaced with `OIDC_` parameters, see [Configuration](configuration.md) and [OpenID Connect authentication](../integrations/oidc_authentication.md) for details.

## Release 0.9.9

**Breaking changes**

* The value of the configuration parameter `MYSQL_AZURE` has been changed from `true` to `flexible` or `single`, depending on the type of Azure Database for MySQL. See [Configuration](configuration.md) for details.

## Release 0.9.1

**Breaking changes**

* The SSLyze parser has been replaced by the CryptoLyzer parser due to licensing reasons. Even though the SSLyze parser may still be seen in the list of parsers, you cannot use it for imports anymore. The CryptoLyter parser generates the same kind of results, adding information about signature algorithms.

* The project name `secobserve_prod` has been set in `docker-compose-prod-mysql.yml` and `docker-compose-prod-postgres.yml`. This was necessary to assign defined network names, but it changes the name of the database volume. You need to dump the database content to a file before the upgrade and restore it after the upgrade.
