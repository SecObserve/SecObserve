from rest_framework.serializers import DateTimeField, IntegerField, Serializer


class ProductMetricsSerializer(Serializer):
    active_critical = IntegerField()
    active_high = IntegerField()
    active_medium = IntegerField()
    active_low = IntegerField()
    active_none = IntegerField()
    active_unknown = IntegerField()
    open = IntegerField()
    affected = IntegerField()
    resolved = IntegerField()
    duplicate = IntegerField()
    false_positive = IntegerField()
    in_review = IntegerField()
    not_affected = IntegerField()
    not_security = IntegerField()
    risk_accepted = IntegerField()


class ProductMetricsStatusSerializer(Serializer):
    last_calculated = DateTimeField()
    calculation_interval = IntegerField()
