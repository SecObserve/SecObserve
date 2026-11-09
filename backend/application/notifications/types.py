class Product_Notification_Type:
    """The kinds of events a user can be notified about, the values are the fields of
    Product_Notification."""

    SECURITY_GATE_CHANGED = "security_gate_changed"
    OBSERVATION_NEW_CHANGED = "observation_new_changed"
    OBSERVATION_TO_BE_REVIEWED = "observation_to_be_reviewed"
    ASSESSMENT_TO_BE_REVIEWED = "assessment_to_be_reviewed"
    ASSESSMENT_APPROVAL_RECEIPT = "assessment_approval_receipt"
    PRODUCT_RULE_TO_BE_REVIEWED = "product_rule_to_be_reviewed"
    PRODUCT_RULE_APPROVAL_RECEIPT = "product_rule_approval_receipt"

    PRODUCT_NOTIFICATION_TYPES = (
        SECURITY_GATE_CHANGED,
        OBSERVATION_NEW_CHANGED,
        OBSERVATION_TO_BE_REVIEWED,
        ASSESSMENT_TO_BE_REVIEWED,
        ASSESSMENT_APPROVAL_RECEIPT,
        PRODUCT_RULE_TO_BE_REVIEWED,
        PRODUCT_RULE_APPROVAL_RECEIPT,
    )


class Webhook_Event_Type:
    OBSERVATION_CREATED = "observation.created"
    OBSERVATION_REVIEW_REQUESTED = "observation.review_requested"
    ASSESSMENT_APPROVAL_REQUESTED = "assessment.approval_requested"
    ASSESSMENT_APPROVAL_DECIDED = "assessment.approval_decided"
    RULE_APPROVAL_REQUESTED = "rule.approval_requested"
    RULE_APPROVAL_DECIDED = "rule.approval_decided"
    IMPORT_COMPLETED = "import.completed"
    SECURITY_GATE_CHANGED = "security_gate.changed"
    WEBHOOK_TEST = "webhook.test"

    SUBSCRIBABLE = [
        OBSERVATION_CREATED,
        OBSERVATION_REVIEW_REQUESTED,
        ASSESSMENT_APPROVAL_REQUESTED,
        ASSESSMENT_APPROVAL_DECIDED,
        RULE_APPROVAL_REQUESTED,
        RULE_APPROVAL_DECIDED,
        IMPORT_COMPLETED,
        SECURITY_GATE_CHANGED,
    ]

    CHOICES = [(event_type, event_type) for event_type in SUBSCRIBABLE + [WEBHOOK_TEST]]


class Webhook_Delivery_Status:
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"

    CHOICES = [
        (PENDING, PENDING),
        (SUCCEEDED, SUCCEEDED),
        (FAILED, FAILED),
    ]
