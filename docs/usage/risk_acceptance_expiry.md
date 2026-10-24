# Assessment expiry

When an observation gets the status `Risk accepted` or `Not affected`, it is possible to set an expiry date for the assessment. After the expiry date, the assessment will automatically be removed, so that the observation is reviewed again.

`Not affected` is often justified by how a product uses a component, e.g. a vulnerable function that is not called. That justification can become wrong when the code changes, while the observation stays the same as long as the component version does not change. The expiry makes sure such an assessment is revisited.

The number of days until the expiry date can be configured separately for `Risk accepted` and `Not affected`, on 3 different levels:

1. In the [Settings](../getting_started/configuration.md#administration-in-secobserve) are the parameters `Risk acceptance expiry (days)` and `Not affected expiry (days)`, which are used if there are no specific settings for Products or Product Groups. Both default to 30 days.
2. Product Groups have the parameters `Risk acceptance expiry` and `Not affected expiry`, which can have 3 values:
    * **Standard**: The standard settings are used for all Products, if nothing specific is configured for a Product.
    * **Disabled**: No expiry date is set, if nothing specific is configured for a Product.
    * **Product group specific**: Use a Product Group specific number of days, if nothing specific is configured for a Product.
3. Products have the parameters `Risk acceptance expiry` and `Not affected expiry` as well, which can have 3 values:
    * **Standard**: The standard settings or Product Group specific settings are used for the Product.
    * **Disabled**: No expiry date is set.
    * **Product specific**: Use a Product specific number of days.

A value of `0` days means that no expiry date is set.

The number of days will be used to set a default for the expiry date when the status `Risk accepted` or `Not affected` is set in an assessment or when manually editing an Observation. This default can be changed or set to empty in the respective dialogs. If a Product Rule or General Rule sets one of these statuses, the default expiry date will be set as well. Changing from `Risk accepted` to `Not affected` or vice versa calculates a new expiry date.

When an assessment is made via the API without the field `risk_acceptance_expiry_date`, the default expiry date is calculated on the server if the status changes, and the existing expiry date is kept if the status stays the same. Sending an empty value for `risk_acceptance_expiry_date` means that no expiry date is set.

The status `Not affected` set by a [VEX statement](../integrations/vex.md) or by a scanner, e.g. Dependency-Track, gets no expiry date, because it is the statement of the VEX issuer or the scanner and is updated by the next import. Administrators can enable the setting `Not affected from VEX or scanners expires` to let these expire as well.

Observations that got the status `Not affected` before the expiry was introduced keep it without an expiry date. An expiry date can be set for them with a new assessment.

---

Per default the task to check the assessment expiry is scheduled to run every night at 01:00 UTC time. This default can be changed by administrators via the **Background tasks** section in the [Settings](../getting_started/configuration.md#administration-in-secobserve).  Hours are in UTC, unless [`TIME_ZONE`](../getting_started/configuration.md#time-zone-of-the-background-tasks) is set.
