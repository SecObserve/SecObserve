# Notifications

SecObserve can send notifications to email addresses, Microsoft Teams or Slack for several kinds of events:

* When a new observation has been stored or an observation has changed.
* When a new observation title has been stored or data of observation with this title has changed.
* When the [security gate](../usage/security_gates.md) of a product changes.
* When an exception occurs while processing a request.
* When an exception occurs in a background task.

There is a ratelimiting active to prevent flooding of notifications, if a series of exceptions occurs. The same exception is sent only once during a specified timedelta, which can be configured in the [Settings](../getting_started/configuration.md#admininistration-in-secobserve). The default for this timedelta is 1 hour.

##  Notifications to email addresses

#### Settings in SecObserve

The field `EMAIL_FROM` needs to be set in the [Settings](../getting_started/configuration.md#admininistration-in-secobserve) to be able to send notifications to email addresses for both events. 

#### Notifications for observations, observation titles and security gates

When creating or editing a product, the field `Email` can be set in the *Notification* section with a comma separated list of email addresses. If the [security gate](../usage/security_gates.md) of the product changes and this field is filled, then a notification is sent each of the email addresses.

![Email notification](../assets/images/screenshot_email.png)

#### Notifications for exceptions

An admistrator can configure the field `EXCEPTION_EMAIL_TO` in the [Settings](../getting_started/configuration.md#admininistration-in-secobserve). If an exception occurs while processing a request and this field is filled with a comma separated list of email addresses, a notifications is sent each of the email addresses before returning the HTTP code 500 via the REST API.

##  Notifications to Microsoft Teams and Slack

####  Settings in Microsoft Teams

For both types of notifications an incoming webhook has to be set for a channel, where the notifications shall appear. How to do this is explained in [Create Incoming Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook). Copy the URL of the webhook to the clipboard, to have it available to set it in SecObserve.

The messages do not include mentions, but a user can set the "Channel notifications" to "All activities" in Teams, to get an active notification when an entry is generated. 

####  Settings in Slack

For both types of notifications an incoming webhook has to be set for a channel, where the notifications shall appear. How to do this is explained in [Sending messages using Incoming Webhooks](https://api.slack.com/messaging/webhooks). Copy the URL of the webhook to the clipboard, to have it available to set it in SecObserve.

#### Notifications for observations, observation titles and security gates

When creating or editing a product, the fields `MS Teams` and/or `Slack` can be set in the *Notification* section with the copied webhook URL. If the [security gate](../usage/security_gates.md) of the product changes and this field is filled, then a notification is sent to Microsoft Teams and/or Slack.

![MS Teams notification](../assets/images/screenshot_ms_teams.png)

#### Notifications for exceptions

An admistrator can configure the fields `EXCEPTION_MS_TEAMS_WEBHOOK` and/or `EXCEPTION_SLACK_WEBHOOK` in the [Settings](../getting_started/configuration.md#admininistration-in-secobserve). If an exception occurs while processing a request and this field is filled with the copied webhook URL, a notifications is sent to Microsoft Teams and/or Slack before returning the HTTP code 500 via the REST API.

## Notifications for observations

To send notifications for new or changed observations, it must be specified in the settings of the Product or the Product Group, which observations will be notified. There are 3 attributes available:

* **Minimum severity:** A notification is send, when the observation has a severity that has at least this severity. Example: If the minimum severity is `High`, there will be a notifications for all observations with severity `Critical` or `High`.
* **Statuses:** A list of statuses the observation must have to be notified. If this field is empty, notifications will be send for the 3 active statuses (`Open`, `Affected`, `In review`).
* **Minimum priority:** A notification is send, when the observation has a priority that has at least this priority. Example: If the minimum priority is `3`, there will be a notifications for all observations with priorities `1`, `2` or `3`.


## Notifications for observation titles

Notifications for observation titles is an aggregation of notifications, by grouping notifications for observations with the same title. To send notifications for titles of new or changed observations, it must be specified in the [SecObserve settings](../getting_started/configuration.md#admininistration-in-secobserve) which observations will be notified. There are 4 attributes available:

* **Minimum severity:** A notification for a title is send, when an observation has a severity that has at least this severity. Example: If the minimum severity is `High`, there will be a notifications for all observations with severity `Critical` or `High`.
* **Statuses:** A list of statuses the observation must have to be notified. If this field is empty, notifications will be send for the 3 active statuses (`Open`, `Affected`, `In review`).
* **Minimum priority:** A notification for a title is send, when an observation has a priority that has at least this priority. Example: If the minimum priority is `3`, there will be a notifications for all observations with priorities `1`, `2` or `3`.
* **Parser type:** A notification for a title is send, when the parser used for this observation has the specified type.


## Notifications in the user interface

Notifications are also stored in the database and can be viewed in the user interface.

* **Regular users** can view notifications for changed security gates and exceptions in background tasks for all products where they are a product member.
* **Administrators** can view all notifications.

![UI notifications](../assets/images/screenshot_notifications.png)

When a notification is deleted, it is removed from the database and won't be visible anymore for all users.
