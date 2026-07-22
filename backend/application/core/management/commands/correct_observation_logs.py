import logging
import traceback
from typing import Any

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db.models import Q

from application.core.models import Observation_Log

logger = logging.getLogger("secobserve.core")


class Command(BaseCommand):

    help = "Correct the rules attributes of Observation Logs"

    def handle(self, *args: Any, **options: Any) -> None:
        logger.info("Correcting rules in Observation Logs ...")

        try:
            observation_logs = (
                Observation_Log.objects.filter(
                    Q(general_rule__isnull=False)
                    | Q(general_rule_rego__isnull=False)
                    | Q(product_rule__isnull=False)
                    | Q(product_rule_rego__isnull=False)
                )
                .select_related("general_rule")
                .select_related("general_rule_rego")
                .select_related("product_rule")
                .select_related("product_rule_rego")
            )

            num_observation_logs = 0

            paginator = Paginator(observation_logs, 1000)
            for page_number in paginator.page_range:
                page = paginator.page(page_number)
                updates = []

                for observation_log in page.object_list:
                    has_change = False
                    if (
                        observation_log.general_rule
                        and observation_log.comment != observation_log.general_rule.description
                    ):
                        observation_log.general_rule = None
                        has_change = True
                    if (
                        observation_log.general_rule_rego
                        and observation_log.comment != observation_log.general_rule_rego.description
                    ):
                        observation_log.general_rule_rego = None
                        has_change = True
                    if (
                        observation_log.product_rule
                        and observation_log.comment != observation_log.product_rule.description
                    ):
                        observation_log.product_rule = None
                        has_change = True
                    if (
                        observation_log.product_rule_rego
                        and observation_log.comment != observation_log.product_rule_rego.description
                    ):
                        observation_log.product_rule_rego = None
                        has_change = True

                    if has_change:
                        updates.append(observation_log)
                        num_observation_logs += 1

                Observation_Log.objects.bulk_update(
                    updates, ["general_rule", "general_rule_rego", "product_rule", "product_rule_rego"]
                )

            logger.info("... %s Observation Logs corrected", num_observation_logs)
        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
