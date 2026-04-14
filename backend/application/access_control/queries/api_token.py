from typing import Optional

from django.db.models.query import QuerySet

from application.access_control.models import API_Token_Multiple, User
from application.access_control.services.current_user import get_current_user


def get_api_token_by_id(pk: int) -> Optional[API_Token_Multiple]:
    try:
        return API_Token_Multiple.objects.get(pk=pk)
    except API_Token_Multiple.DoesNotExist:
        return None


def get_api_tokens() -> QuerySet[API_Token_Multiple]:
    user = get_current_user()

    if user is None:
        return API_Token_Multiple.objects.none()

    api_tokens = API_Token_Multiple.objects.all().order_by("id")

    if user.is_superuser:
        return api_tokens

    return api_tokens.filter(user=user)


def get_api_tokens_for_user(given_user: User) -> QuerySet[API_Token_Multiple]:
    current_user = get_current_user()

    if current_user is None:
        return API_Token_Multiple.objects.none()

    api_tokens = API_Token_Multiple.objects.filter(user=given_user).order_by("id")

    if current_user.is_superuser:
        return api_tokens

    return api_tokens if current_user == given_user else API_Token_Multiple.objects.none()
