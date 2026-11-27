from rest_framework.serializers import ModelSerializer

from application.audit_trail.models import Product_Audit_Event


class ProductAuditEventSerializer(ModelSerializer):
    class Meta:
        model = Product_Audit_Event
        fields = "__all__"
