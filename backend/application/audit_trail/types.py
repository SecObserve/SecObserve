class Audit_Action:
    CREATED = "Created"
    CHANGED = "Changed"
    DELETED = "Deleted"
    # Approvals use the approval status as action, e.g. "Approved", "Approved with edits" or "Rejected"


class Audit_Object_Type:
    PRODUCT = "Product"
    BRANCH = "Branch"
    SERVICE = "Service"
    PRODUCT_RULE = "Product rule"
    API_CONFIGURATION = "API configuration"
    PRODUCT_MEMBER = "Product member"
    PRODUCT_AUTHORIZATION_GROUP_MEMBER = "Product authorization group member"
    SCANCODEIO_PROJECT = "ScanCode.io project"
    WEBHOOK = "Webhook"
    ASSESSMENT = "Assessment"

    OBJECT_TYPE_CHOICES = [
        (PRODUCT, PRODUCT),
        (BRANCH, BRANCH),
        (SERVICE, SERVICE),
        (PRODUCT_RULE, PRODUCT_RULE),
        (API_CONFIGURATION, API_CONFIGURATION),
        (PRODUCT_MEMBER, PRODUCT_MEMBER),
        (PRODUCT_AUTHORIZATION_GROUP_MEMBER, PRODUCT_AUTHORIZATION_GROUP_MEMBER),
        (SCANCODEIO_PROJECT, SCANCODEIO_PROJECT),
        (WEBHOOK, WEBHOOK),
        (ASSESSMENT, ASSESSMENT),
    ]
