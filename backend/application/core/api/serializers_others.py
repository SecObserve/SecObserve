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
    # has_observations and has_licenses are annotated in get_components()
    has_observations = BooleanField(read_only=True)
    has_licenses = BooleanField(read_only=True)

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
