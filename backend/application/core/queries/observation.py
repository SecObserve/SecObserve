import re
from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Branch,
    Evidence,
    Observation,
    Observation_Log,
    Potential_Duplicate,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)


def get_observation_by_id(observation_id: int) -> Optional[Observation]:
    try:
        return Observation.objects.get(id=observation_id)
    except Observation.DoesNotExist:
        return None


def get_observations() -> QuerySet[Observation]:
    user = get_current_user()

    if user is None:
        return Observation.objects.none()

    observations = Observation.objects.all().order_by("id")

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product__product_group"),
            authorization_group__users=user,
        )

        observations = observations.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        observations = observations.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    return observations


def get_observations_for_vulnerability_check(
    product: Product,
    branch: Optional[Branch],
    service: Optional[Service],
    filename: str,
    api_configuration_name: str,
) -> QuerySet[Observation]:
    # The import reads the service of every observation, the product it sets itself
    observations = Observation.objects.select_related("origin_service")

    if filename or api_configuration_name:
        return observations.filter(
            product=product,
            branch=branch,
            origin_service=service,
            upload_filename=filename,
            api_configuration_name=api_configuration_name,
        )

    if service:
        return observations.filter(
            product=product,
            branch=branch,
            origin_service=service,
            upload_filename="",
            api_configuration_name="",
            origin_service__name=service,
        ).order_by("id")

    return observations.filter(
        product=product,
        branch=branch,
        origin_service=service,
        upload_filename="",
        api_configuration_name="",
        origin_service__isnull=True,
    ).order_by("id")


def get_evidences() -> QuerySet[Evidence]:
    user = get_current_user()

    if user is None:
        return Evidence.objects.none()

    evidences = Evidence.objects.all().order_by("id")

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("observation__product_id"), user=user)
        product_group_members = Product_Member.objects.filter(
            product=OuterRef("observation__product__product_group"), user=user
        )

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product__product_group"),
            authorization_group__users=user,
        )

        evidences = evidences.annotate(
            observation__product__member=Exists(product_members),
            observation__product__product_group__member=Exists(product_group_members),
            observation__product__authorization_group_member=Exists(product_authorization_group_members),
            observation__product__product_group_authorization_group_member=Exists(
                product_group_authorization_group_members
            ),
        )

        evidences = evidences.filter(
            Q(observation__product__member=True)
            | Q(observation__product__product_group__member=True)
            | Q(observation__product__authorization_group_member=True)
            | Q(observation__product__product_group_authorization_group_member=True)
        )

    return evidences


def get_potential_duplicates() -> QuerySet[Potential_Duplicate]:
    user = get_current_user()

    if user is None:
        return Potential_Duplicate.objects.none()

    potential_duplicates = Potential_Duplicate.objects.all().order_by("id")

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("observation__product_id"), user=user)
        product_group_members = Product_Member.objects.filter(
            product=OuterRef("observation__product__product_group"), user=user
        )

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product__product_group"),
            authorization_group__users=user,
        )

        potential_duplicates = potential_duplicates.annotate(
            observation__product__member=Exists(product_members),
            observation__product__product_group__member=Exists(product_group_members),
            observation__product__authorization_group_member=Exists(product_authorization_group_members),
            observation__product__product_group_authorization_group_member=Exists(
                product_group_authorization_group_members
            ),
        )

        potential_duplicates = potential_duplicates.filter(
            Q(observation__product__member=True)
            | Q(observation__product__product_group__member=True)
            | Q(observation__product__authorization_group_member=True)
            | Q(observation__product__product_group_authorization_group_member=True)
        )

    return potential_duplicates


def get_observation_log_by_id(observation_log_id: int) -> Optional[Observation_Log]:
    try:
        return Observation_Log.objects.get(id=observation_log_id)
    except Observation_Log.DoesNotExist:
        return None


def get_observation_logs() -> QuerySet[Observation_Log]:
    user = get_current_user()

    if user is None:
        return Observation_Log.objects.none()

    observation_logs = Observation_Log.objects.all().order_by("id")

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("observation__product_id"), user=user)
        product_group_members = Product_Member.objects.filter(
            product=OuterRef("observation__product__product_group"), user=user
        )

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("observation__product__product_group"),
            authorization_group__users=user,
        )

        observation_logs = observation_logs.annotate(
            observation__product__member=Exists(product_members),
            observation__product__product_group__member=Exists(product_group_members),
            observation__product__authorization_group_member=Exists(product_authorization_group_members),
            observation__product__product_group_authorization_group_member=Exists(
                product_group_authorization_group_members
            ),
        )

        observation_logs = observation_logs.filter(
            Q(observation__product__member=True)
            | Q(observation__product__product_group__member=True)
            | Q(observation__product__authorization_group_member=True)
            | Q(observation__product__product_group_authorization_group_member=True)
        )

    return observation_logs


def get_current_observation_log(observation: Observation) -> Optional[Observation_Log]:
    try:
        return Observation_Log.objects.filter(observation=observation).latest("created")
    except Observation_Log.DoesNotExist:
        return None


def get_modifying_observation_logs() -> QuerySet[Observation_Log]:
    return Observation_Log.objects.filter(
        ~Q(status="") | ~Q(severity="") | ~Q(vex_justification="") | ~Q(vex_remediations__isnull=True)
    )


def get_current_modifying_observation_log(observation: Observation) -> Optional[Observation_Log]:
    prefetched_logs = getattr(observation, "_vex_modifying_logs", None)
    if prefetched_logs is not None:
        return prefetched_logs[0] if prefetched_logs else None

    try:
        return get_modifying_observation_logs().filter(observation_id=observation.id).latest("created")
    except Observation_Log.DoesNotExist:
        return None


# The fields must be the same as the ones of the trigram indexes in
# migration 0101_observation_full_text_search, otherwise not all searched fields are indexed.
OBSERVATION_FULL_TEXT_SEARCH_FIELDS = [
    "title",
    "description",
    "recommendation",
    "vulnerability_id",
    "vulnerability_id_aliases",
    "origin_component_name_version",
    "origin_docker_image_name_tag",
    "origin_endpoint_url",
    "origin_source_file",
    "origin_cloud_qualified_resource",
    "origin_kubernetes_qualified_resource",
]
OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS = ["comment"]

# A term in double quotes is matched as a whole word, all other characters except whitespace as part of a word.
# Unbalanced double quotes are ignored.
FULL_TEXT_SEARCH_TERM_PATTERN = re.compile(r'"([^"]*)"|([^\s"]+)')


def _get_full_text_search_terms(value: str) -> list[tuple[str, bool]]:
    terms = []
    for quoted_term, term in FULL_TEXT_SEARCH_TERM_PATTERN.findall(value):
        if term:
            terms.append((term, False))
        elif quoted_term.strip():
            terms.append((quoted_term.strip(), True))
    return terms


def _get_full_text_search_filter(fields: list[str], term: str, whole_word: bool) -> Q:
    # Not preceded or followed by a letter, digit or underscore, works for PostgreSQL and Python (SQLite)
    whole_word_regex = rf"(?<!\w){re.escape(term)}(?!\w)"

    full_text_search_filter = Q()
    for field in fields:
        # icontains is needed for whole words as well, because only icontains can use the trigram indexes.
        # The regular expression is then only checked for the rows found with the indexes.
        field_filter = Q(**{f"{field}__icontains": term})
        if whole_word:
            field_filter &= Q(**{f"{field}__iregex": whole_word_regex})
        full_text_search_filter |= field_filter
    return full_text_search_filter


def filter_observations_full_text(queryset: QuerySet[Observation], value: str) -> QuerySet[Observation]:
    # All terms must be found, each of them either in the texts of the observation or in a comment of its log
    for term, whole_word in _get_full_text_search_terms(value):
        matching_observations = Observation.objects.filter(
            _get_full_text_search_filter(OBSERVATION_FULL_TEXT_SEARCH_FIELDS, term, whole_word)
        ).values("id")
        matching_observation_logs = Observation_Log.objects.filter(
            _get_full_text_search_filter(OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS, term, whole_word)
        ).values("observation_id")

        # A union instead of an OR condition, because PostgreSQL can use the indexes of both tables only this way
        queryset = queryset.filter(id__in=matching_observations.union(matching_observation_logs))

    return queryset
