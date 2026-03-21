from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from application.commons.models import Settings
from application.core.types import Status


class VersionSerializer(Serializer):
    version = CharField(max_length=200)


class StatusSettingsSerializer(Serializer):
    features = ListField(child=CharField(), min_length=0, max_length=200, required=True)
    risk_acceptance_expiry_days = IntegerField()
    vex_justification_style = CharField()


class SettingsSerializer(ModelSerializer):
    id = SerializerMethodField()
    observation_title_notification_status_list = ListField(
        child=CharField(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Settings
        exclude = ["observation_title_notification_statuses"]

    def get_id(self, obj: Settings) -> int:  # pylint: disable=unused-argument
        # obj is needed for the signature but we don't need it
        # The id is hardcoded to 1 because there is only one instance of the Settings model
        return 1

    def validate_observation_title_notification_status_list(self, value: list[str]) -> list[str]:
        if not isinstance(value, list):
            raise ValidationError("Status list must be a list of strings")

        invalid_statuses = []
        for status in value:
            if status not in Status.STATUS_LIST:
                invalid_statuses.append(status)

        if invalid_statuses:
            raise ValidationError(f"Invalid statuses: {', '.join(invalid_statuses)}")

        return value

    def to_representation(self, instance: Settings) -> dict[str, Any]:
        data = super().to_representation(instance)

        data["observation_title_notification_status_list"] = (
            instance.observation_title_notification_statuses.split(",")
            if instance.observation_title_notification_statuses
            else []
        )
        return data

    def to_internal_value(self, data: dict) -> dict:
        validated_data = super().to_internal_value(data)

        if "observation_title_notification_status_list" in validated_data:
            statuses = validated_data["observation_title_notification_status_list"]
            if isinstance(statuses, list):
                validated_data["observation_title_notification_statuses"] = ",".join(statuses)

        return validated_data
