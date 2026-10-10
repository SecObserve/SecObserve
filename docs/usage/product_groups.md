# Product groups

A *product group* is a collection of products. It is used to group products that belong together, e.g. because they are part of the same project.

Users can not only see the list of the associated products, their observations and their combined metrics, but there are some settings that are shared between all products of the group:

* **Rules** defined for a product group are applied to all products in the group in addition to the rules defined for the product.
* **Members** defined for a product group have access to the products in the group in addition to the members defined for the product.
* The **API token** of a product group can be used to access the API for all products in the group.
* **Housekeeping for branches / versions:**
    * *Standard:* The branches / versions of all products in the group are deleted according to the settings of the product.
    * *Disabled:* Housekeeping for branches / versions is disabled for all products in the group.
    * *Product group specific:* The branches / versions of all products in the group are deleted according to the settings of the product group.
* The settings for **Notifications** are used, if no notification settings are defined for the product. If there are notification settings defined for the product, they override the settings of the product group. This applies to the notification settings of the product as well as to the [user specific notifications](notifications.md#user-specific-notifications).
*  **Security gates:**
    * *Standard:* The security gates of all products in the group are calculated according to the settings of the product.
    * *Disabled:* Security gates are disabled for all products in the group.
    * *Product group specific:* Security gates of all products in the group are calculated according to the settings of the product group.

## Observations

The *Observations* tab of a product group shows the observations of all products in the group. By default, it shows the active observations of the default branches, the same scope as the counts in the header of the product group. The filters and columns are the same as in the list of all observations.

The `Export` menu of the product group exports the current selection of the *Observations* tab to an Excel or CSV file, with the filters and the sort order of the list. These entries are shown when the *Observations* tab is open.
