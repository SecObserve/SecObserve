from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from application.core.services.full_text_search import (
    FullTextSearchError,
    activate_full_text_search,
    deactivate_full_text_search,
)

ACTION_ACTIVATE = "activate"
ACTION_DEACTIVATE = "deactivate"


class Command(BaseCommand):

    help = "Activate or deactivate the full text search for observations, including its database indexes"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "action",
            choices=[ACTION_ACTIVATE, ACTION_DEACTIVATE],
            help="activate: create the indexes and show the search, deactivate: hide the search and drop the indexes",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            if options["action"] == ACTION_ACTIVATE:
                activate_full_text_search()
                self.stdout.write("Full text search activated")
            else:
                deactivate_full_text_search()
                self.stdout.write("Full text search deactivated")
        except FullTextSearchError as e:
            raise CommandError(str(e)) from e
