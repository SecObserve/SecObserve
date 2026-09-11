# Risk acceptance expiry

When an observation gets the status `Risk accepted`, it is possible to set an expiry date for the acceptance. After the expiry date, the assessment with the risk acceptance will automatically be removed.

The number of days until the expiry date can be configured on 3 different levels:

1. In the [Settings](../getting_started/configuration.md#administration-in-secobserve) is the parameter `Risk acceptance expiry (days)`, which is used if there are no specific settings for Products or Product Groups.
2. Product Groups have the parameter `Risk acceptance expiry`, which can have 3 values:
    * **Standard**: The standard settings are used for all Products, if nothing specific is configured for a Product.
    * **Disabled**: No expiry date is set for the risk acceptance, if nothing specific is configured for a Product.
    * **Product group specific**: Use a Product Group specific value for `Risk acceptance expiry (days)`, if nothing specific is configured for a Product.
3. Products have the parameter `Risk acceptance expiry` as well, which can have 3 values:
    * **Standard**: The standard settings or Product Group specific settings are used for the Product.
    * **Disabled**: No expiry date is set for the risk acceptance.
    * **Product specific**: Use a Product specific value for `Risk acceptance expiry (days)`.

A value of `0` for the `Risk acceptance expiry (days)` means that no expiry date is set for the risk acceptance.

The number of `Risk acceptance expiry (days)` will be used to set a default for the expiry date when the status `Risk accepted` is set in an assessment or when manually editing an Observation. This default can be changed or set to empty in the respective dialogs. If a Product Rule or General Rule sets the status of an Observation to `Risk accepted`, the default expiry date will be set as well.

---

Per default the task to check the risk acceptance expiry is scheduled to run every night at 01:00 UTC time. This default can be changed by administrators via the **Background tasks** section in the [Settings](../getting_started/configuration.md#administration-in-secobserve).  Hours are always in UTC time.
