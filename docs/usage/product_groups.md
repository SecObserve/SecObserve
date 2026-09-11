# Product groups

A *product group* is a collection of products. It is used to group products that belong together, e.g. because they are part of the same project.

Users cannot see only the list of the associated products and their combined metrics, but there are some settings that are shared between all products of the group:

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
