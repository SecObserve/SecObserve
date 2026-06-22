# Users, groups and permissions

## Users

![Sign In](../assets/images/screenshot_sign_in.png){ width="40%" style="display: block; margin: 0 auto" }

SecObserve supports two types of users:

* **Internally managed users**: You need a username and password given by a SecObserve administrator and use the `SIGN IN WITH USER` button.
* **Users managed in a directory:** The button `ENTERPRISE SIGN` will redirect you to login page of your users directory, if [OpenID Connect](../integrations/oidc_authentication.md) is configured.

Users have specified permissions depending on their type and role in a product.

## User types

The user type can be set by flags in the user administration:

* **Superusers** are the administrators of the system.
* **External users** do not belong to the organization, e.g. customers or partners.
* **Internal users** are all users who are not superusers or external users.

When a user logs in with an OIDC account for the first time, it can be automatically determined whether it is an internal or external user by their email address. The parameter `Internal users` in the [Settings](../getting_started/configuration.md#admininistration-in-secobserve) takes a comma-separated list of email of regular expression. If one regular expression matches the email address of the user, the user is considered an internal user. If no regular expression matches, the user is considered an external user.

There are some general permissions based on the user's type:

|                             | Internal | External | Superuser |
|-----------------------------|:--------:|:--------:|:---------:|
| Create Product Groups       | X        | -        | X         |
| Create Product              | X        | -        | X         |
|                             |          |          |           |
| View General Rules          | X        | X        | X         |
| Create General Rules        | -        | -        | X         |
| Edit General Rules          | -        | -        | X         |
| Delete General Rules        | -        | -        | X         |
|                             |          |          |           |
| Change own password ^1)^    | X        | X        | X         |
| Change all passwords  ^1)^  | -        | -        | X         |
| Manage users                | -        | -        | X         |
| Create authorization groups | X        | -        | X         |
| Manage authorization groups | X ^2)^   | X ^2)^   | X         |
|                             |          |          |           |
| Import VEX documents        | -        | -        | X         |
| Manage VEX counters         | -        | -        | X         |
|                             |          |          |           |
| Manage Settings             | -        | -        | X         |
| Reset JWT secret            | -        | -        | X         |

**^1)^** Not for OIDC users

**^2)^** Only if the user is a manager of the authorization group


## Authorization groups

Authorization groups are used to manage permissions for multiple users at once. Users can be added to authorization groups and the groups can be assigned to products. This way, permissions can be managed centrally for multiple users.

Authorization groups can be mapped to OIDC group claims. If the OICD token includes a group claim (see [OpenID Connect authentication](../integrations/oidc_authentication.md)), the user will automatically be added to the authorization group, where an entry of the group claim matches the attribute `oidc_group`. If the users will be removed from the group in the user directory, the user will be removed from the authorization group automatically as well.


## Roles and permissions

![Product Members](../assets/images/screenshot_product_members.png)

While superusers have permission to view and edit all data, internal and external users must be either a user member or member of an authorization group with a specific role to access the product and its data. User members and authorization group members of a product group have access to all products of that group with their respective role.

|                          | Reader | Writer | Maintainer | Owner | Upload |
|--------------------------|:------:|:------:|:----------:|:-----:|:------:|
| View Product Group       | X      | X      | X          | X     | -      |
| Edit Product Group       | -      | -      | X          | X     | -      |
| Delete Product Group     | -      | -      | -          | X     | -      |
|                          |        |        |            |       |        |
| View Product             | X      | X      | X          | X     | -      |
| Import Observations      | -      | X      | X          | X     | X      |
| Edit Product             | -      | -      | X          | X     | -      |
| Delete Product           | -      | -      | -          | X     | -      |
|                          |        |        |            |       |        |
| View Observation         | X      | X      | X          | X     | -      |
| Create Observation       | -      | X      | X          | X     | -      |
| Edit Observation ^1)^    | -      | X      | X          | X     | -      |
| Assess Observation       | -      | X      | X          | X     | -      |
| Delete Observation       | -      | -      | -          | X     | -      |
|                          |        |        |            |       |        |
| View Product Rules       | X      | X      | X          | X     | -      |
| Create Product Rules     | -      | -      | X          | X     | -      |
| Edit Product Rules       | -      | -      | X          | X     | -      |
| Apply Rules to Product   | -      | -      | X          | X     | -      |
| Delete Product Rules     | -      | -      | X          | X     | -      |
|                          |        |        |            |       |        |
| View API Configuration   | X      | X      | X          | X     | -      |
| Create API Configuration | -      | -      | X          | X     | -      |
| Edit API Configuration   | -      | -      | X          | X     | -      |
| Delete API Configuration | -      | -      | X          | X     | -      |
|                          |        |        |            |       |        |
| View User Member         | X      | X      | X          | X     | -      |
| Create User Member       | -      | -      | X ^2)^     | X     | -      |
| Edit User Member         | -      | -      | X ^2)^     | X     | -      |
| Delete User Member       | -      | -      | X ^2)^     | X     | -      |
|                          |        |        |            |       |        |
| View Authorization Group Member   | X      | X      | X          | X     | -      |
| Create Authorization Group Member | -      | -      | X ^2)^     | X     | -      |
| Edit Authorization Group Member   | -      | -      | X ^2)^     | X     | -      |
| Delete Authorization Group Member | -      | -      | X ^2)^     | X     | -      |
|                          |        |        |            |       |        |
| View VEX                 | X      | X      | X          | X     | -      |
| Create VEX ^3)^          | -      | -      | X          | X     | -      |
| Edit VEX ^3)^            | -      | -      | X          | X     | -      |
| Delete VEX^3)^           | -      | -      | X          | X     | -      |

**^1)^** Only manually created observations can be edited

**^2)^** Maintainers are not allowed to manipulate Owners of that product

**^3)^** Only for VEX documents (CSAF or OpenVEX) linked to a product. For VEX documents without a product, the user who created the VEX document is the owner of the document and can perform all actions on it.


## Management of users and authorization groups

Users and authorization groups can be managed by superusers in the Access Control administration:

![Settings / Access Control](../assets/images/screenshot_settings_access_control.png)
