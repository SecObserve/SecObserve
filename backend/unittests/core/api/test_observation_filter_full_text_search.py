from unittest.mock import patch

from django.core.management import call_command
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.api.filters import ObservationFilter
from application.core.models import Observation, Observation_Log
from application.core.queries.observation import (
    OBSERVATION_FULL_TEXT_SEARCH_FIELDS,
    _get_full_text_search_terms,
)
from application.core.types import Observation_Log_Comment
from application.rules.models import Rule
from application.rules.types import Rule_Type
from unittests.base_test_case import BaseTestCase


class TestObservationFilterFullTextSearch(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )
        super().setUpClass()

    def setUp(self):
        super().setUp()
        Settings(feature_full_text_search=True).save()

    def test_not_postgresql(self):
        with self.assertRaises(ValidationError) as e:
            ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", "injection")

        self.assertEqual(["Full text search is not activated"], e.exception.detail)

    @patch("application.commons.services.functions.connection")
    def test_postgresql_not_activated(self, mock_connection):
        mock_connection.vendor = "postgresql"
        Settings(feature_full_text_search=False).save()

        with self.assertRaises(ValidationError) as e:
            ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", "injection")

        self.assertEqual(["Full text search is not activated"], e.exception.detail)

    def test_not_postgresql_api(self):
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            response = APIClient().get("/api/observations/?full_text_search=injection")

        self.assertEqual(400, response.status_code)
        self.assertEqual({"message": "Full text search is not activated"}, response.data)

    @patch("application.commons.services.functions.connection")
    def test_postgresql(self, mock_connection):
        mock_connection.vendor = "postgresql"

        queryset = ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", "jection")

        sql = str(queryset.query)
        for field in OBSERVATION_FULL_TEXT_SEARCH_FIELDS:
            self.assertIn(f'"U0"."{field}" LIKE %jection%', sql)
        self.assertIn(" UNION ALL ", sql)
        self.assertIn('FROM "core_observation_log" "U0" WHERE', sql)
        for field in ["general_rule_id", "general_rule_rego_id", "product_rule_id", "product_rule_rego_id"]:
            self.assertIn(f'"U0"."{field}" IS NULL', sql)
        self.assertIn('"U0"."vex_statement_id" IS NULL', sql)
        self.assertIn(
            f'NOT ("U0"."comment" IN ({", ".join(Observation_Log_Comment.FULL_TEXT_SEARCH_EXCLUDED_COMMENTS)}))', sql
        )
        for prefix in Observation_Log_Comment.FULL_TEXT_SEARCH_EXCLUDED_COMMENT_PREFIXES:
            self.assertIn(f'NOT ("U0"."comment" LIKE {prefix}%', sql)
        self.assertIn('"U0"."comment" LIKE %jection%', sql)

    @patch("application.commons.services.functions.connection")
    def test_postgresql_whole_word(self, mock_connection):
        mock_connection.vendor = "postgresql"

        queryset = ObservationFilter().get_full_text_search(
            Observation.objects.all(), "full_text_search", '"sql" jection'
        )

        sql = str(queryset.query)
        for field in OBSERVATION_FULL_TEXT_SEARCH_FIELDS:
            self.assertIn(f'"U0"."{field}" LIKE %sql%', sql)
            self.assertIn(f'"U0"."{field}" REGEXP \'(?i)\' || (?<!\\w)sql(?!\\w)', sql)
            self.assertIn(f'"U0"."{field}" LIKE %jection%', sql)
        self.assertEqual(2, sql.count(" UNION ALL "))

    def _search(self, value):
        with patch("application.commons.services.functions.connection") as mock_connection:
            mock_connection.vendor = "postgresql"
            queryset = ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", value)
        return [observation.title for observation in queryset]

    def test_postgresql_result_part_of_word(self):
        self.assertEqual(["db_observation_external_active"], self._search("BSERVATION_EXTERNAL"))

    def test_postgresql_result_whole_word(self):
        self.assertEqual([], self._search('"external"'))
        self.assertEqual(["db_observation_external_active"], self._search('"DB_OBSERVATION_EXTERNAL_ACTIVE"'))

    def test_postgresql_result_all_terms(self):
        self.assertEqual(["db_observation_external_active"], self._search('external "db_observation_external_active"'))
        self.assertEqual([], self._search("external xyz_not_there"))

    def test_postgresql_result_no_terms(self):
        self.assertEqual(Observation.objects.count(), len(self._search(' "" ')))

    def test_postgresql_result_short_terms(self):
        self.assertEqual(Observation.objects.count(), len(self._search('cv "ab" x')))
        self.assertEqual(["db_observation_external_active"], self._search("ab external"))

    def _create_observation_log(self, comment, general_rule=None, product_rule=None):
        Observation_Log.objects.create(
            observation=Observation.objects.get(title="db_observation_external_active"),
            user=User.objects.get(username="db_admin"),
            severity="",
            status="",
            comment=comment,
            general_rule=general_rule,
            product_rule=product_rule,
        )

    def test_postgresql_result_observation_log(self):
        self._create_observation_log("Accepted by the zebra team")

        self.assertEqual(["db_observation_external_active"], self._search("zebra"))
        self.assertEqual(["db_observation_external_active"], self._search('external "zebra team"'))

    def test_postgresql_result_observation_log_excluded(self):
        self._create_observation_log(Observation_Log_Comment.COMMENT_RISK_ACCEPTANCE_EXPIRED)
        self._create_observation_log(Observation_Log_Comment.COMMENT_CREATED_MANUALLY)
        self._create_observation_log(Observation_Log_Comment.COMMENT_CHANGED_MANUALLY)
        self._create_observation_log("Removed product fields rule giraffe_1")
        self._create_observation_log("Removed general rego rule giraffe_2")
        self._create_observation_log("Removed VEX statement from giraffe_3")
        self._create_observation_log("giraffe_4", product_rule=Rule.objects.get(name="db_product_rule_external"))
        self._create_observation_log("giraffe_5", general_rule=Rule.objects.get(name="db_general_rule"))

        # The fixtures contain the comment "Set by parser" for other observations
        self.assertEqual([], self._search("parser"))
        self.assertEqual([], self._search("expired"))
        self.assertEqual([], self._search("manually"))
        for i in range(1, 6):
            self.assertEqual([], self._search(f"giraffe_{i}"))

    def test_postgresql_result_observation_log_written_by_user(self):
        # Similar to comments written by the system, but written by a user
        comments = [
            "Removed product zebra_1 from scope",
            "Removed general zebra_2 access to the endpoint",
            "Removed unknown rule zebra_3 from the WAF",
            "Removed unknown VEX statement zebra_4 from the file",
            "Updated by product owner zebra_5",
        ]
        for i, comment in enumerate(comments, start=1):
            self._create_observation_log(comment)
            self.assertEqual(["db_observation_external_active"], self._search(f"zebra_{i}"))

    def test_postgresql_result_observation_log_removed_rule(self):
        comments = ["Removed product rule giraffe_legacy", "Removed general rule giraffe_legacy"]
        for rule_type, _ in Rule_Type.RULE_TYPE_CHOICES:
            comments.append(f"Removed product {rule_type.lower()} rule giraffe_{rule_type}")
            comments.append(f"Removed general {rule_type.lower()} rule giraffe_{rule_type}")

        for comment in comments:
            self._create_observation_log(comment)

        self.assertEqual([], self._search("giraffe"))

    def test_postgresql_result_observation_log_exact_comments(self):
        self._create_observation_log(Observation_Log_Comment.COMMENT_REMOVED_UNKNOWN_RULE)
        self._create_observation_log(Observation_Log_Comment.COMMENT_REMOVED_UNKNOWN_VEX_STATEMENT)

        self.assertEqual([], self._search('"Removed unknown"'))

    def test_postgresql_result_observation_log_deleted_rule(self):
        # A rule can only be deleted when it is not set in an observation anymore, but the logs still refer to it
        observation = Observation.objects.get(title="db_observation_external_active")
        rule = Rule.objects.create(
            name="giraffe_1", product=observation.product, parser=observation.parser, type=Rule_Type.RULE_TYPE_FIELDS
        )
        self._create_observation_log(
            f"{Observation_Log_Comment.COMMENT_PREFIX_UPDATED_BY_PRODUCT_RULE}giraffe_1", product_rule=rule
        )

        rule.delete()

        observation_log = Observation_Log.objects.get(comment__endswith="giraffe_1")
        self.assertIsNone(observation_log.product_rule)
        self.assertEqual([], self._search("giraffe_1"))

    def test_postgresql_result_observation_log_foreign_key_set_to_null(self):
        self._create_observation_log(f"{Observation_Log_Comment.COMMENT_PREFIX_UPDATED_BY_GENERAL_RULE}giraffe_1")
        self._create_observation_log(
            f"{Observation_Log_Comment.COMMENT_PREFIX_UPDATED_BY_VEX_STATEMENT}giraffe_2\n\nimpact"
        )

        self.assertEqual([], self._search("giraffe_1"))
        self.assertEqual([], self._search("giraffe_2"))

    def test_get_full_text_search_terms(self):
        self.assertEqual([("sql", False), ("injection", False)], _get_full_text_search_terms(" sql  injection "))
        self.assertEqual([("sql", True)], _get_full_text_search_terms('"sql"'))
        self.assertEqual([("sql injection", True)], _get_full_text_search_terms('" sql injection "'))
        self.assertEqual(
            [("xss", False), ("sql", True), ("injection", False)],
            _get_full_text_search_terms('xss "sql" injection'),
        )
        self.assertEqual([("sql", False), ("inj", False)], _get_full_text_search_terms('"sql inj'))
        self.assertEqual([("CVE-2021-44228", False)], _get_full_text_search_terms("CVE-2021-44228"))
        self.assertEqual([], _get_full_text_search_terms('"" "  "'))
        self.assertEqual([], _get_full_text_search_terms(""))

    def test_get_full_text_search_terms_short(self):
        self.assertEqual([("xss", False), ("a b", True)], _get_full_text_search_terms('ab xss "cd" x "a b"'))

    def test_get_full_text_search_terms_max(self):
        terms = [f"term_{i}" for i in range(12)]
        self.assertEqual([(term, False) for term in terms[:10]], _get_full_text_search_terms(" ".join(terms)))
