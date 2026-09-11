class Product_Notification_Type:
    """The kinds of events a user can be notified about, the values are the fields of
    Product_Notification."""

    SECURITY_GATE_CHANGED = "security_gate_changed"
    OBSERVATION_NEW_CHANGED = "observation_new_changed"
    OBSERVATION_TO_BE_REVIEWED = "observation_to_be_reviewed"
    ASSESSMENT_TO_BE_REVIEWED = "assessment_to_be_reviewed"
    ASSESSMENT_APPROVAL_RECEIPT = "assessment_approval_receipt"
    PRODUCT_RULE_TO_BE_REVIEWED = "product_rule_to_be_reviewed"

    PRODUCT_NOTIFICATION_TYPES = (
        SECURITY_GATE_CHANGED,
        OBSERVATION_NEW_CHANGED,
        OBSERVATION_TO_BE_REVIEWED,
        ASSESSMENT_TO_BE_REVIEWED,
        ASSESSMENT_APPROVAL_RECEIPT,
        PRODUCT_RULE_TO_BE_REVIEWED,
    )
