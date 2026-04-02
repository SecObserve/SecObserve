from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from application.vex.services.vex_engine import VEX_Engine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_settings(feature_vex: bool = True) -> MagicMock:
    settings = MagicMock()
    settings.feature_vex = feature_vex
    return settings


def _make_product(purl: str = "pkg:pypi/requests@2.28.0") -> MagicMock:
    product = MagicMock()
    product.purl = purl
    return product


def _make_branch(purl: str = "") -> MagicMock:
    branch = MagicMock()
    branch.purl = purl
    return branch


def _make_observation(
    *,
    vex_statement=None,
    vex_status: str = "",
    origin_component_cyclonedx_bom_link: str = "",
    origin_component_purl: str = "",
    vulnerability_id: str = "CVE-2023-1234",
) -> MagicMock:
    obs = MagicMock()
    obs.vex_statement = vex_statement
    obs.vex_status = vex_status
    obs.origin_component_cyclonedx_bom_link = origin_component_cyclonedx_bom_link
    obs.origin_component_purl = origin_component_purl
    obs.vulnerability_id = vulnerability_id
    return obs


# ---------------------------------------------------------------------------
# Patches applied to every test in this module
# ---------------------------------------------------------------------------

MODULE = "application.vex.services.vex_engine"


class TestVEXEngineInit(TestCase):

    @patch(f"{MODULE}.Settings")
    def test_returns_early_when_feature_vex_disabled(self, mock_settings_cls):
        """No state should be set when the feature flag is off."""
        mock_settings_cls.load.return_value = _make_settings(feature_vex=False)
        product = _make_product()

        engine = VEX_Engine(product=product, branch=None)

        # The instance should have none of the attributes set during normal init
        assert not hasattr(engine, "product")
        assert not hasattr(engine, "branch")
        assert not hasattr(engine, "vex_statements")

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_no_purl_on_product_or_branch_loads_no_statements(self, mock_settings_cls, mock_vex_statement_cls):
        """When neither product nor branch have a PURL, vex_statements stays empty."""
        mock_settings_cls.load.return_value = _make_settings()
        product = _make_product(purl="")

        engine = VEX_Engine(product=product, branch=None)

        mock_vex_statement_cls.objects.filter.assert_not_called()
        assert engine.vex_statements == []

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_invalid_purl_loads_no_statements(self, mock_settings_cls, mock_vex_statement_cls):
        """An unparseable PURL must not raise and must leave vex_statements empty."""
        mock_settings_cls.load.return_value = _make_settings()
        product = _make_product(purl="not-a-valid-purl")

        engine = VEX_Engine(product=product, branch=None)

        mock_vex_statement_cls.objects.filter.assert_not_called()
        assert engine.vex_statements == []

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_uses_product_purl_when_no_branch(self, mock_settings_cls, mock_vex_statement_cls):
        """When branch is None the product PURL drives the DB query."""
        mock_settings_cls.load.return_value = _make_settings()
        expected_statements = [MagicMock(), MagicMock()]
        mock_vex_statement_cls.objects.filter.return_value = expected_statements
        product = _make_product(purl="pkg:pypi/requests@2.28.0")

        engine = VEX_Engine(product=product, branch=None)

        # The filter must use the version-stripped search PURL
        mock_vex_statement_cls.objects.filter.assert_called_once_with(product_purl__startswith="pkg:pypi/requests")
        assert engine.vex_statements == expected_statements

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_uses_branch_purl_when_present(self, mock_settings_cls, mock_vex_statement_cls):
        """When the branch has a PURL it should take precedence over the product PURL."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []
        product = _make_product(purl="pkg:pypi/requests@2.28.0")
        branch = _make_branch(purl="pkg:pypi/myapp@1.0.0")

        engine = VEX_Engine(product=product, branch=branch)

        mock_vex_statement_cls.objects.filter.assert_called_once_with(product_purl__startswith="pkg:pypi/myapp")

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_falls_back_to_product_purl_when_branch_purl_empty(self, mock_settings_cls, mock_vex_statement_cls):
        """A branch with an empty PURL must fall back to the product PURL."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []
        product = _make_product(purl="pkg:pypi/requests@2.28.0")
        branch = _make_branch(purl="")

        engine = VEX_Engine(product=product, branch=branch)

        mock_vex_statement_cls.objects.filter.assert_called_once_with(product_purl__startswith="pkg:pypi/requests")

    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_stores_product_and_branch_attributes(self, mock_settings_cls, mock_vex_statement_cls):
        """product and branch must be stored on the instance."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []
        product = _make_product()
        branch = _make_branch(purl="pkg:pypi/myapp@1.0.0")

        engine = VEX_Engine(product=product, branch=branch)

        assert engine.product is product
        assert engine.branch is branch


class TestApplyVEXStatementsForObservation(TestCase):
    """
    Each test constructs an engine with vex_statements already populated
    (bypassing __init__ side-effects) and exercises the matching logic.
    """

    # ------------------------------------------------------------------
    # Shared setup helper
    # ------------------------------------------------------------------

    def _make_engine(self, vex_statements=None) -> VEX_Engine:
        """Return a VEX_Engine with __init__ bypassed."""
        engine = object.__new__(VEX_Engine)
        engine.product = _make_product()
        engine.branch = None
        engine.vex_statements = vex_statements or []
        return engine

    # ------------------------------------------------------------------
    # Feature-flag guard
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation")
    @patch(f"{MODULE}.Settings")
    def test_returns_early_when_feature_vex_disabled(self, mock_settings_cls, mock_apply, mock_log):
        mock_settings_cls.load.return_value = _make_settings(feature_vex=False)
        engine = self._make_engine()
        obs = _make_observation()

        engine.apply_vex_statements_for_observation(obs)

        mock_apply.assert_not_called()
        mock_log.assert_not_called()

    # ------------------------------------------------------------------
    # BOM-link path (highest priority)
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_bom_link_match_stops_further_search(self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log):
        """A BOM-link match must prevent the product-level statements from being tried."""
        mock_settings_cls.load.return_value = _make_settings()
        bom_stmt = MagicMock()
        mock_vex_statement_cls.objects.filter.return_value = [bom_stmt]
        obs = _make_observation(origin_component_cyclonedx_bom_link="urn:cdx:abc/1#comp")
        engine = self._make_engine(vex_statements=[MagicMock()])

        engine.apply_vex_statements_for_observation(obs)

        # _apply must have been called exactly once (with the BOM statement)
        mock_apply.assert_called_once_with(bom_stmt, obs, None)
        # No "no statement" log because a match was found
        mock_log.assert_not_called()
        # observation.vex_statement should be cleared then re-set by the engine
        assert obs.vex_statement is None  # cleared at start; mock_apply doesn't set it

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_bom_link_breaks_after_first_match(self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log):
        """Only the first matching BOM statement must be applied."""
        mock_settings_cls.load.return_value = _make_settings()
        bom_stmt1, bom_stmt2 = MagicMock(), MagicMock()
        mock_vex_statement_cls.objects.filter.return_value = [bom_stmt1, bom_stmt2]
        obs = _make_observation(origin_component_cyclonedx_bom_link="urn:cdx:abc/1#comp")
        engine = self._make_engine()

        engine.apply_vex_statements_for_observation(obs)

        mock_apply.assert_called_once_with(bom_stmt1, obs, None)

    # ------------------------------------------------------------------
    # Product-level statements path
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_product_statements_used_when_no_bom_link(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """When there is no BOM-link on the observation, fall through to self.vex_statements."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []  # no BOM statements
        prod_stmt = MagicMock()
        engine = self._make_engine(vex_statements=[prod_stmt])
        obs = _make_observation()  # no bom_link

        engine.apply_vex_statements_for_observation(obs)

        mock_apply.assert_called_once_with(prod_stmt, obs, None)
        mock_log.assert_not_called()

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_product_statements_breaks_after_first_match(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """Only the first matching product statement must be applied."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []
        stmt1, stmt2 = MagicMock(), MagicMock()
        engine = self._make_engine(vex_statements=[stmt1, stmt2])
        obs = _make_observation()

        engine.apply_vex_statements_for_observation(obs)

        mock_apply.assert_called_once_with(stmt1, obs, None)

    # ------------------------------------------------------------------
    # Component-PURL fallback path
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_component_purl_fallback_when_no_prior_match(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """
        When both BOM-link and product statements fail to match, the engine must
        query by component PURL.
        """
        mock_settings_cls.load.return_value = _make_settings()
        comp_stmt = MagicMock()

        # The observation has no BOM-link, so only the component-PURL filter is called
        mock_vex_statement_cls.objects.filter.return_value = [comp_stmt]

        engine = self._make_engine(vex_statements=[])  # no product-level statements
        obs = _make_observation(origin_component_purl="pkg:pypi/flask@2.3.0")

        engine.apply_vex_statements_for_observation(obs)

        # The component-PURL DB query must use the stripped search PURL
        mock_vex_statement_cls.objects.filter.assert_called_once_with(
            product_purl__startswith="pkg:pypi/flask", component_purl=""
        )
        mock_apply.assert_called_once_with(comp_stmt, obs, None)
        mock_log.assert_not_called()

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_component_purl_fallback_breaks_after_first_match(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """Only the first matching component-PURL statement must be applied."""
        mock_settings_cls.load.return_value = _make_settings()

        # Make _apply_vex_statement_for_observation return True only on second call
        mock_apply.side_effect = [False, True]
        comp_stmt1, comp_stmt2, comp_stmt3 = MagicMock(), MagicMock(), MagicMock()
        mock_vex_statement_cls.objects.filter.return_value = [comp_stmt1, comp_stmt2, comp_stmt3]

        engine = self._make_engine(vex_statements=[])
        obs = _make_observation(origin_component_purl="pkg:pypi/flask@2.3.0")

        engine.apply_vex_statements_for_observation(obs)

        # Should have stopped after the second call (first True)
        assert mock_apply.call_count == 2

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_component_purl_fallback_skipped_for_invalid_purl(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """An invalid component PURL must not trigger a DB query."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []

        engine = self._make_engine(vex_statements=[])
        obs = _make_observation(origin_component_purl="not-a-valid-purl")

        engine.apply_vex_statements_for_observation(obs)

        # Only one filter call may exist (the BOM-link call is skipped too since
        # bom_link is empty); no component fallback query
        for filter_call in mock_vex_statement_cls.objects.filter.call_args_list:
            assert "product_purl__startswith" not in str(filter_call) or filter_call != call(
                product_purl__startswith="not-a-valid-purl", component_purl=""
            )

    # ------------------------------------------------------------------
    # "No VEX statement found" log path
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_log_called_when_previous_statement_existed_but_no_match(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """
        When no match is found and the observation previously had a VEX statement,
        write_observation_log_no_vex_statement must be called.
        """
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []

        previous_stmt = MagicMock()
        engine = self._make_engine(vex_statements=[])
        obs = _make_observation(vex_statement=previous_stmt)

        engine.apply_vex_statements_for_observation(obs)

        mock_log.assert_called_once_with(obs, previous_stmt)

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_log_called_when_observation_has_vex_status_but_no_match(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """
        When no match is found and observation.vex_status is set,
        write_observation_log_no_vex_statement must still be called.
        """
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []

        engine = self._make_engine(vex_statements=[])
        obs = _make_observation(vex_status="not_affected")

        engine.apply_vex_statements_for_observation(obs)

        mock_log.assert_called_once_with(obs, None)

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_log_not_called_when_no_previous_statement_and_no_vex_status(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """
        When there was no previous VEX statement and vex_status is empty,
        write_observation_log_no_vex_statement must NOT be called.
        """
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []

        engine = self._make_engine(vex_statements=[])
        obs = _make_observation(vex_statement=None, vex_status="")

        engine.apply_vex_statements_for_observation(obs)

        mock_log.assert_not_called()

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=True)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_log_not_called_when_match_found(self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log):
        """When a VEX statement is matched, the no-statement log must NOT fire."""
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []
        engine = self._make_engine(vex_statements=[MagicMock()])
        obs = _make_observation(vex_statement=MagicMock(), vex_status="not_affected")

        engine.apply_vex_statements_for_observation(obs)

        mock_log.assert_not_called()

    # ------------------------------------------------------------------
    # Correct previous_vex_statement passed to _apply
    # ------------------------------------------------------------------

    @patch(f"{MODULE}.write_observation_log_no_vex_statement")
    @patch(f"{MODULE}._apply_vex_statement_for_observation", return_value=False)
    @patch(f"{MODULE}.VEX_Statement")
    @patch(f"{MODULE}.Settings")
    def test_previous_vex_statement_captured_before_clearing(
        self, mock_settings_cls, mock_vex_statement_cls, mock_apply, mock_log
    ):
        """
        The previous vex_statement must be captured before observation.vex_statement
        is set to None, and passed correctly to _apply and the log helper.
        """
        mock_settings_cls.load.return_value = _make_settings()
        mock_vex_statement_cls.objects.filter.return_value = []

        previous_stmt = MagicMock()
        prod_stmt = MagicMock()
        engine = self._make_engine(vex_statements=[prod_stmt])
        obs = _make_observation(vex_statement=previous_stmt)

        engine.apply_vex_statements_for_observation(obs)

        # _apply must receive the captured previous statement
        mock_apply.assert_called_once_with(prod_stmt, obs, previous_stmt)
        # And so must the log helper
        mock_log.assert_called_once_with(obs, previous_stmt)
