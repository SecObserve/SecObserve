# Assessments, approvals and reviews

## Assessment

With an assessment of an observation the user can change two attributes of an observation:

* The **severity** given by the parser must not necessarily match the severity of the observation for the current product.
* All observations have initially the **status** `Open`. The result of an investigation how to deal with the observation might say,
    * the product is `Affected` by the observation, 

    or the observation must not be fixed because it is ...

    * ... `In review` and needs further investigation.
    * ... already `Resolved`. You have to be aware that the observation will be set back to `Open` if it will be found in a subsequent import.
    * ... a `Duplicate` of another observation.
    * ... a `False positive` that has been detected by the scanner wrongly.
    * ... `Risk accepted`, a decision that a breach because of that observation can be managed.
    * The system is `Not affected` because the observation has been mitigated by a measure.

The dialog to enter the assessment can be opened when showing the observation: 

![Start assessment](../assets/images/screenshot_assessment_1.png)

In the assessment dialog the user can change either the severity and/or the status and has to enter a mandatory comment to explain the change:

![Assessment](../assets/images/screenshot_assessment_2.png){ width="60%" style="display: block; margin: 0 auto" }

A new entry with the changed values is stored in the `Observation Log` after the assessment has been saved.

## Approvals

With the default settings of the product, the assessment is activated right away. If more control is needed, the product can be configured to require an approval before the assessment is activated. This can be done while creating or editing a product:

![Assessments need approval](../assets/images/screenshot_assessments_need_approval.png){ width="60%" style="display: block; margin: 0 auto" }

The setting is also available for product groups. If it is set for a product group, it will be inherited by all products in that group.

If the approval is required, the dialog showing the observation or and the dialog showing the observation log (after clicking on an entry in the list of observation logs) will show a button to either approve or reject the assessment:

![Show observation log](../assets/images/screenshot_observation_log_show.png)

Be aware, that the user who has created the assessment is not allowed to approve or reject it. The approval must be done by another user.

![Assessment approval](../assets/images/screenshot_assessment_approval.png){ width="60%" style="display: block; margin: 0 auto" }

## Reviews

To make it easier to find observations with the status `In Review` or assessements needing an approval, a tab is shown for the product, if reviews or approvals are pending:

![Reviews tab](../assets/images/screenshot_reviews_tab.png)
