from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from application.core.models import Component


class ComponentSerializer(ModelSerializer):
    name_version_type = SerializerMethodField()
    # has_observations and has_licenses are annotated in get_components()
    has_observations = BooleanField(read_only=True)
    has_licenses = BooleanField(read_only=True)

    def get_name_version_type(self, obj: Component) -> str:
        if obj.name_version:
            name_version_type = obj.name_version
            if obj.purl_type:
                name_version_type += f" ({obj.purl_type})"
            return name_version_type
        return ""

    class Meta:
        model = Component
        fields = "__all__"


class ComponentNameSerializer(ModelSerializer):
    class Meta:
        model = Component
        fields = ["id", "name_version"]


class PURLTypeElementSerializer(Serializer):
    id = CharField()
    name = CharField()


class PURLTypeSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=PURLTypeElementSerializer())
