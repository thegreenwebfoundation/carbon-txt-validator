"""Tests for ArelleSessionManager and ArelleProcessor changes.

These tests exercise the new session reuse infrastructure and the
modified ArelleProcessor that uses skipDTS + a manual facts index.
"""

import pathlib

import pytest
from arelle import ModelXbrl  # type: ignore

import carbon_txt.processors.csrd_document as csrd_module
from carbon_txt.exceptions import NoLoadableCSRDFile
from carbon_txt.processors.csrd_document import (
    ArelleProcessor,
    ArelleSessionManager,
    get_shared_session_manager,
)

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"
LOCAL_FILE_1 = str(FIXTURE_DIR / "esrs-e1-efrag-2026-12-31-en.xhtml")
LOCAL_FILE_2 = str(FIXTURE_DIR / "esrs-e2-efrag-2026-12-31-en-no-renewables.xhtml")


@pytest.fixture(autouse=True)
def reset_shared_session_manager():
    """Reset the module-level shared session manager between tests to avoid
    cross-test thread issues (Arelle Sessions are thread-bound)."""
    old = csrd_module._shared_session_manager
    if old is not None:
        try:
            old.close()
        except Exception:  # noqa
            pass
    csrd_module._shared_session_manager = None
    yield
    if csrd_module._shared_session_manager is not None:
        try:
            csrd_module._shared_session_manager.close()
        except Exception:  # noqa
            pass
    csrd_module._shared_session_manager = None


# ---------------------------------------------------------------------------
# ArelleSessionManager
# ---------------------------------------------------------------------------


class TestArelleSessionManager:
    """Tests for the session reuse manager."""

    def test_load_valid_report(self):
        """load_report() returns a ModelXbrl for a valid local file."""
        mgr = ArelleSessionManager()
        try:
            model = mgr.load_report(LOCAL_FILE_1)
            assert isinstance(model, ModelXbrl.ModelXbrl)
        finally:
            mgr.close()

    def test_raises_on_unloadable_file(self):
        """load_report() raises NoLoadableCSRDFile for a bad URL."""
        mgr = ArelleSessionManager()
        try:
            with pytest.raises(NoLoadableCSRDFile):
                mgr.load_report("https://www.example.com/no-csrd-report")
        finally:
            mgr.close()

    def test_reuses_session(self):
        """Calling load_report() twice reuses the same internal session."""
        mgr = ArelleSessionManager()
        try:
            mgr.load_report(LOCAL_FILE_1)
            session_after_first = mgr._session
            assert session_after_first is not None

            mgr.load_report(LOCAL_FILE_2)
            session_after_second = mgr._session
            assert session_after_second is session_after_first
        finally:
            mgr.close()

    def test_loads_multiple_distinct_reports(self):
        """Two sequential load_report() calls return distinct, valid models."""
        mgr = ArelleSessionManager()
        try:
            model_1 = mgr.load_report(LOCAL_FILE_1)
            model_2 = mgr.load_report(LOCAL_FILE_2)

            assert model_1 is not model_2
            assert isinstance(model_1, ModelXbrl.ModelXbrl)
            assert isinstance(model_2, ModelXbrl.ModelXbrl)

            # Verify they have different fact counts (file 1 is larger)
            facts_1 = list(model_1.facts)
            facts_2 = list(model_2.facts)
            assert len(facts_1) > len(facts_2)
        finally:
            mgr.close()

    def test_close_is_idempotent(self):
        """Calling close() twice does not raise."""
        mgr = ArelleSessionManager()
        mgr.load_report(LOCAL_FILE_1)
        mgr.close()
        mgr.close()  # should not raise

    def test_recovers_after_close(self):
        """After close(), a new load_report() creates a fresh session."""
        mgr = ArelleSessionManager()
        try:
            mgr.load_report(LOCAL_FILE_1)
            mgr.close()
            assert mgr._session is None

            # Should work again with a new session
            model = mgr.load_report(LOCAL_FILE_1)
            assert isinstance(model, ModelXbrl.ModelXbrl)
            assert mgr._session is not None
        finally:
            mgr.close()


class TestGetSharedSessionManager:
    """Tests for the module-level singleton."""

    def test_returns_singleton(self):
        """get_shared_session_manager() returns the same instance each time."""
        mgr_1 = get_shared_session_manager()
        mgr_2 = get_shared_session_manager()
        assert mgr_1 is mgr_2


# ---------------------------------------------------------------------------
# ArelleProcessor changes
# ---------------------------------------------------------------------------


class TestArelleProcessorChanges:
    """Tests for the modified ArelleProcessor."""

    def test_accepts_custom_session_manager(self):
        """ArelleProcessor can be given an explicit session manager."""
        mgr = ArelleSessionManager()
        try:
            processor = ArelleProcessor(LOCAL_FILE_1, session_manager=mgr)
            assert processor.parsed_reports()
        finally:
            mgr.close()

    def test_facts_by_local_name_index_populated(self):
        """The manual _facts_by_local_name index contains expected codes."""
        mgr = ArelleSessionManager()
        try:
            processor = ArelleProcessor(LOCAL_FILE_1, session_manager=mgr)

            expected_codes = [
                "PercentageOfRenewableSourcesInTotalEnergyConsumption",
                "EnergyConsumptionFromRenewableSources",
                "EnergyConsumptionRelatedToOwnOperations",
            ]
            for code in expected_codes:
                assert code in processor._facts_by_local_name, (
                    f"{code} not found in facts index"
                )
                assert len(processor._facts_by_local_name[code]) > 0
        finally:
            mgr.close()

    def test_xbrls_property_backward_compat(self):
        """The .xbrls property returns a list with one model."""
        mgr = ArelleSessionManager()
        try:
            processor = ArelleProcessor(LOCAL_FILE_1, session_manager=mgr)
            xbrls = processor.xbrls
            assert isinstance(xbrls, list)
            assert len(xbrls) == 1
            assert isinstance(xbrls[0], ModelXbrl.ModelXbrl)
        finally:
            mgr.close()


# ---------------------------------------------------------------------------
# Plugin early-exit paths
# ---------------------------------------------------------------------------


class TestPluginEarlyExit:
    """Tests for early-exit paths in the process_csrd_document plugin."""

    def test_plugin_skips_non_esef_extension(self):
        """A csrd-report disclosure with a .pdf URL returns early without Arelle."""
        from carbon_txt.process_csrd_document import process_document
        from carbon_txt.schemas.common import Disclosure

        doc = Disclosure(
            doc_type="csrd-report",
            url="https://example.com/report.pdf",
            domain="example.com",
        )
        logs = []
        result = process_document(document=doc, logs=logs)

        # Should return early with just logs, no plugin_name or document_results
        assert "plugin_name" not in result
        assert any("ESEF-compatible" in log for log in logs)

    def test_plugin_skips_unreachable_url(self, httpx_mock):
        """A csrd-report with an unreachable HTTPS URL returns early after HEAD fails."""
        from carbon_txt.process_csrd_document import process_document
        from carbon_txt.schemas.common import Disclosure

        url = "https://unreachable.example.com/report.xhtml"
        httpx_mock.add_response(url=url, method="HEAD", status_code=404)

        doc = Disclosure(
            doc_type="csrd-report",
            url=url,
            domain="unreachable.example.com",
        )
        logs = []
        result = process_document(document=doc, logs=logs)

        assert "plugin_name" not in result
        assert any("failed pre-validation" in log for log in logs)

    def test_plugin_processes_valid_local_csrd(self, httpx_mock):
        """End-to-end: the plugin processes a local .xhtml file and returns datapoints.

        We use a mock HTTP URL whose HEAD returns a plausible ESEF content-type,
        but pass the local file path to the processor via a patched URL so Arelle
        loads the fixture directly.
        """
        from unittest.mock import patch

        from carbon_txt.process_csrd_document import process_document
        from carbon_txt.schemas.common import Disclosure

        url = "https://example.com/report.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "application/xhtml+xml"},
        )
        # Content sniffing does a GET — must return iXBRL markers
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            content=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>iXBRL report</body></html>',
        )

        doc = Disclosure(
            doc_type="csrd-report",
            url=url,
            domain="test.example.com",
        )
        logs = []

        # The HTTP HEAD pre-check uses the URL, but Arelle needs to load the
        # local fixture file. We patch document.url just for the Arelle call
        # by intercepting the GreenwebCSRDProcessor to use the local file.
        with patch(
            "carbon_txt.process_csrd_document.GreenwebCSRDProcessor"
        ) as mock_proc_class:
            from carbon_txt.processors.csrd_document import (
                ArelleProcessor,
            )
            from carbon_txt.processors.csrd_document import (
                GreenwebCSRDProcessor as RealProcessor,
            )

            real_arelle = ArelleProcessor(LOCAL_FILE_1)
            real_proc = RealProcessor(arelle_processor=real_arelle)
            mock_proc_class.return_value = real_proc

            result = process_document(document=doc, logs=logs)

        assert result["plugin_name"] == "csrd_greenweb"
        assert len(result["document_results"]) > 0

        # Check we got actual DataPoint objects back
        from carbon_txt.processors.csrd_document import DataPoint

        datapoints = [r for r in result["document_results"] if isinstance(r, DataPoint)]
        assert len(datapoints) > 0
        # Verify a known datapoint is present
        renewable_pct = [
            dp
            for dp in datapoints
            if dp.short_code == "PercentageOfRenewableSourcesInTotalEnergyConsumption"
        ]
        assert len(renewable_pct) > 0
        assert renewable_pct[0].value > 0.2
