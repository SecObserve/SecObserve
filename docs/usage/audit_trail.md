# Audit trail

The audit trail records who changed the configuration of a Product or Product Group, when it happened and what was changed. It also records the decisions on approvals of assessments and Product Rules.

## What is recorded

Events are recorded when one of these objects of a Product or Product Group is created, changed or deleted:

| Object type | Remarks |
|-------------|---------|
| Product | Includes Product Groups, changes of the default branch, the assessment approvers and the Products in a Product Group |
| Branch | |
| Service | |
| Product rule | Approvals are recorded as separate events |
| API configuration | |
| Product member | Includes the users of Product API tokens |
| Product authorization group member | |
| ScanCode.io project | Only created and deleted |
| Webhook | |
| Assessment | Only approvals |

Each event shows:

* **Created**: Date and time of the event.
* **Object type** and **Name** of the object.
* **Action**: `Created`, `Changed` or `Deleted`. For approvals it is the decision: `Approved`, `Approved with edits` or `Rejected`.
* **User**: The user who made the change. It is empty for changes made by background tasks. The name is kept when the user is deleted later, e.g. when an API token is revoked.

Clicking on an event with details expands it:

* **Created** events show the values that have been set, without the fields that still have their default value.
* **Changed** events show the old and the new value of each changed field.
* **Approvals** show the rejection remark and, for `Approved with edits`, the edited fields of the assessment.

Some values are not shown in clear text:

* Secrets like API keys, passwords, webhook URLs and webhook secrets are shown as `***`, even if they have been changed.
* Long texts are cut after 255 characters.

Changes made by imports and by the background tasks, like the date of the last import or the status of the security gate, are not recorded. The history of observations is not part of the audit trail, it is shown in the observation log of each observation.

When a Product is deleted, only the deletion of the Product itself is recorded, not the deletion of its Branches, Services, Rules, etc. The events of the Product are kept after its deletion.

## Viewing the audit trail

The audit trail of a Product or Product Group can be found in the tab **Audit Trail** in its settings. It can be filtered by date, object type and name. Users need the role `Maintainer` or `Owner` for the Product to see the audit trail, see [Roles and permissions](users_permissions.md#roles-and-permissions).

Superusers have an additional entry **Audit Trail** in the administration section of the navigation bar. It shows the events of all Products and Product Groups, including those that have been deleted, and can be filtered by Product and user as well.

## Events from before the audit trail

Events are only recorded since the audit trail has been introduced. When upgrading, existing approvals of assessments are added to the audit trail, for Product Rules only the latest approval, because SecObserve kept no older history with user and date.

## Disabling the audit trail

The audit trail is enabled by default. It can be disabled with `Enable audit trail` in the `Features` section of the [Settings](../getting_started/configuration.md#administration-in-secobserve). No events are recorded while it is disabled and the audit trail is hidden in the user interface. Events recorded before stay in the database.
