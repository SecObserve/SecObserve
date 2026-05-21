from typing import Any, Optional

from django.apps import apps
from django.db.models.fields import CharField, TextField
from rest_framework.exceptions import ValidationError

from application.commons.models import Settings


def get_classname(obj: Any) -> str:
    cls = type(obj)
    module = cls.__module__
    name = cls.__qualname__
    if module != "__builtin__":
        name = module + "." + name
    return name


def get_base_url_frontend() -> str:
    settings = Settings.load()
    base_url_frontend = settings.base_url_frontend
    if not base_url_frontend.endswith("/"):
        base_url_frontend += "/"
    return base_url_frontend


def clip_fields(application: str, model: str, my_object: Any) -> None:
    Model = apps.get_model(application, model)
    for field in Model._meta.get_fields():
        if isinstance(field, (CharField, TextField)):
            _, _, _, key_args = field.deconstruct()
            max_length = key_args.get("max_length")
            if max_length:
                value = getattr(my_object, field.name)
                if value and len(value) > max_length:
                    setattr(my_object, field.name, value[: max_length - 4] + " ...")
                    value = getattr(my_object, field.name)
                    if value.count("```") == 1:
                        # There is an open code block, that we have to close
                        setattr(
                            my_object,
                            field.name,
                            value[: max_length - 9] + "\n```\n\n...",
                        )


def get_comma_separated_as_list(comma_separated_string: str) -> list[str]:
    return_list = comma_separated_string.split(",") if comma_separated_string else []
    return [x.strip() for x in return_list]


def validate_vex_remediations(value: Any) -> Optional[list[dict]]:
    """
    Validate that vex_remediations is either None or a list of dictionaries
    where each dictionary contains 'category' and 'text' fields with string values.
    """
    if value is None:
        return value

    items = []

    if not isinstance(value, list):
        raise ValidationError("vex_remediations must be a list or null.")

    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("Each item must be a dictionary.")

        if "category" not in item and "text" not in item:
            continue

        if "category" not in item or "text" not in item:
            raise ValidationError("Each item must contain the fields 'category' and 'text'.")

        if not isinstance(item["category"], str):
            raise ValidationError("The 'category' field must be a string.")

        if not isinstance(item["text"], str):
            raise ValidationError("The 'text' field must be a string.")

        items.append(item)

    if items:
        return items

    return None
