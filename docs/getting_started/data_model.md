# Data model

## Vulnerability Management

``` mermaid
erDiagram
    Product_Group |o--o{ Product : has
    Product ||--o{ Observation : has
    Product ||--o{ Branch_Version : has
    Product ||--o{ Service : has
    Product ||--o{ Vulnerability_Check : has
    Product ||--o{ Product_Rule : has
    Product ||--o{ API_Configuration : has
    Product ||--o{ Product_Member : has
    Product ||--o{ Product_Authorization_Group_Member : has
    Parser ||--o{ Observation: discovered_by
    Observation }o--o| Branch_Version: found_in
    Observation }o--o| Component : references
    Observation ||--|{ Observation_Log : has
    Observation ||--|{ Reference : has
    Observation ||--|{ Evidence : has
    General_Rule
```

#### Product Group

A `Product Group` is a collection of products. It is used to group products that belong together, e.g. because they are part of the same project. In the database, the product groups are stored in the table `Product` with the flag `is_product_group` set to `true`.

#### Product

A `Product` is the representation of the system that is checked for vulnerabilities.

#### Observation

An `Observation` is something that has been discovered by a vulnerability scanner. Not every observation is actually a vulnerability. An assessment can show it is e.g. a false positive or not applicable in the current context.

Every `Observation` belongs to exactly one product.

#### Component

A `Component` is a library, package or other building block that is used in a product. Components are created automatically during imports and are identified by their Package URL, resp. by their name and version if there is no Package URL.

Contrary to most other entities, a `Component` does not belong to a product. It exists once for the whole SecObserve instance and is referenced by the observations and license components of all products it is used in. See more in [Components](../usage/components.md).

#### Branch / Version

Software development often uses branches in the source code repository and software is often available in multiple versions. Vulnerability scanners can run for different branches / versions of a product and observations can be viewed and managed by branch / version. See more in [branches and Versions](../usage/branches.md).

#### Service

A `Service` is a self-contained piece of functionality of a product. Can be something like a microservice or `backend` or `frontend`.	

#### Vulnerability Check

An import for one product, one branch / version and one file name resp. one API configuration is a so-called vulnerability check. See more in [Import algorithm](../usage/import_observations.md#import-algorithm).

#### Parser

SecObserve can parse a variety of data formats, written by vulnerability scanners. Besides file-based parsers, SecObserve implements API-based parsers as well, which get data directly from a system via REST calls. See more about vulnerability scanners and parsers on [Supported scanners](../integrations/supported_scanners.md).

#### Observation Log

Every change of the severity or the status of an observation is recorded in the `Observation Log`.

#### Reference

`References` are links to further information about the observation. They are imported with the observation.

#### Evidence

`Evidences` are extracts from the scan reports showing the basis on which the observation was created.

#### Product Rule / General Rule

Rules can change the severity or the status of an observation can be changed during the import. An example would be to set a risk acceptance automatically for observations that shall not be fixed. `General Rules` will be applied for all products, while `Product Rules` are only valid for one product. See more about rules on [Rule engine](../usage/rule_engine.md).

#### API Configuration

Parsers who get data from vulnerability scanners via a REST API need a configuration how to access the API (URL, API key, ...). The `API Configuration` is set per product.

#### Product Member

`Product Members` define which users have access to a product. Depending on the role of a user for a product, they have more or less functionality available, see more on [Users and permissions](../usage/users_permissions.md).

#### Product Authorization Group Member

`Product Authorization Group Members` define which authorization groups have access to a product. Depending on the role, the users of the authorization group have more or less functionality available, see more on [Users and permissions](../usage/users_permissions.md).


## License Management

``` mermaid
erDiagram
    Product ||--o{ Branch_Version : has
    Product ||--o{ License_Component : has
    Branch_Version }o--o| License_Policy : references
    Product }o--o| License_Policy : references
    Product_Group }o--o| License_Policy : references
    License_Component }o--o| License : references
    License_Component }o--o| Component : references
    License_Component ||--|{ License_Component_Evidence : has
    License_Policy }o--o| License_Policy : parent
    License_Policy ||--o{ License_Policy_Item : has
    License_Policy ||--o{ License_Policy_Member : has
    License_Policy ||--o{ License_Policy_Authorization_Group_Member : has
    License_Group }o--o{ License : references
    License_Group ||--o{ License_Group_Member : has
    License_Group ||--o{ License_Group_Authorization_Group_Member : has
    License_Policy_Item }o--o| License : references
    License_Policy_Item }o--o| License_Group : references
```
#### License

The [Linux Foundation](https://www.linuxfoundation.org/) gathers a list of commonly found licenses and exceptions used for open source and other collaborative software. The list is called [SPDX License List](https://spdx.org/licenses/) and is imported daily into SecObserve.

#### License Component

A `License Component` is the usage of a [Component](#component) in a product. It is licensed under a specific license and has an evaluation of the license according to a license policy. Depending on the license information in the scan report, there are 3 different types of licenses:

* a license with a known SPDX identifier
* a license expression, if the license expression in the scan report is valid [according to the SPDX specification](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/) and consists only of known SPDX identifiers
* a non-spdx license string in all other cases

#### License Component Evidence

`License Component Evidences` are extracts from the scan reports showing the basis on which the license component was created.

#### License Policy

A `License Policy` defines the rules for the usage of licenses in a product. It can define which licenses are allowed, which are forbidden, and which need a review.

A `License Policy` can have another license policy as a `Parent`. If a license policy has a parent, the rules of the parent are also valid for the child policy, but existing rules of the parent can be overriden and new rules can be added. 

#### License Policy Item

A `License Policy Item` is a single rule in a license policy. It can be a rule for a specific license, a rule for a license group or a rule for a non-spdx license string, e.g. a license that is not in the SPDX list or a license expression.

#### License Policy Member

`License Policy Members` define which users have access to a license policy, either read-only or as a manager.

#### License Policy Authorization Group Member

`License Policy Authorization Group Members` define which authorization groups have access to a license policy, either read-only or as a manager.

#### License Group

A `License Group` is a collection of licenses with similar license conditions. There is a predefined list of license groups, taken from the classification of the [Blue Oak Council](https://blueoakcouncil.org/).

#### License Group Member

`License Group Members` define which users have access to a license group, either read-only or as a manager.

#### License Group Authorization Group Member

`License Group Authorization Group Members` define which authorization groups have access to a license group, either read-only or as a manager.
