"""Tests for CSRD pre-validation helpers.

These functions provide fast, cheap checks before invoking the expensive
Arelle XBRL processor.
"""

import httpx
import pytest

from carbon_txt.process_csrd_document import (
    _looks_like_esef_url,
    _quick_validate_remote_csrd_url,
)


# ---------------------------------------------------------------------------
# _looks_like_esef_url
# ---------------------------------------------------------------------------


class TestLooksLikeEsefUrl:
    """URL extension heuristic for ESEF-compatible documents."""

    def test_looks_like_esef_xhtml(self):
        assert _looks_like_esef_url("https://example.com/report.xhtml") is True

    def test_looks_like_esef_xbrl(self):
        assert _looks_like_esef_url("https://example.com/report.xbrl") is True

    def test_looks_like_esef_xml(self):
        assert _looks_like_esef_url("https://example.com/report.xml") is True

    def test_looks_like_esef_zip(self):
        assert _looks_like_esef_url("https://example.com/report.zip") is True

    def test_looks_like_esef_html(self):
        assert _looks_like_esef_url("https://example.com/report.html") is True

    def test_looks_like_esef_htm(self):
        assert _looks_like_esef_url("https://example.com/report.htm") is True

    def test_looks_like_esef_extensionless(self):
        """Extensionless URLs are allowed through (might serve correct content)."""
        assert _looks_like_esef_url("https://example.com/report") is True

    def test_rejects_pdf(self):
        assert _looks_like_esef_url("https://example.com/report.pdf") is False

    def test_rejects_csv(self):
        assert _looks_like_esef_url("https://example.com/data.csv") is False

    def test_rejects_image(self):
        assert _looks_like_esef_url("https://example.com/logo.png") is False

    def test_case_insensitive(self):
        """Extension check is case-insensitive."""
        assert _looks_like_esef_url("https://example.com/REPORT.XHTML") is True

    def test_local_file_path(self):
        assert _looks_like_esef_url("/path/to/report.xhtml") is True


# ---------------------------------------------------------------------------
# _quick_validate_remote_csrd_url
# ---------------------------------------------------------------------------


class TestQuickValidateRemoteCsrdUrl:
    """Lightweight HTTP HEAD pre-validation for remote CSRD URLs."""

    def test_prevalidate_local_path_always_passes(self):
        """Local file paths bypass HTTP checks entirely."""
        assert _quick_validate_remote_csrd_url("/path/to/file.xhtml") is True

    def test_prevalidate_reachable_xhtml_passes(self, httpx_mock):
        """A reachable URL with an HTML-family content-type passes."""
        url = "https://example.com/report.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "text/html"},
        )
        assert _quick_validate_remote_csrd_url(url) is True

    def test_prevalidate_404_fails(self, httpx_mock):
        """A 404 response causes pre-validation to fail."""
        url = "https://example.com/missing.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=404,
        )
        assert _quick_validate_remote_csrd_url(url) is False

    def test_prevalidate_wrong_content_type_fails(self, httpx_mock):
        """A 200 with an incompatible content-type (e.g. PDF) fails."""
        url = "https://example.com/report.pdf"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "application/pdf"},
        )
        assert _quick_validate_remote_csrd_url(url) is False

    def test_prevalidate_empty_content_type_passes(self, httpx_mock):
        """A 200 with no content-type header is allowed through."""
        url = "https://example.com/report.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            # No content-type header
        )
        assert _quick_validate_remote_csrd_url(url) is True

    def test_prevalidate_connection_error_fails(self, httpx_mock):
        """A connection error causes pre-validation to fail."""
        url = "https://unreachable.example.com/report.xhtml"
        httpx_mock.add_exception(
            httpx.ConnectError("Connection refused"),
            url=url,
            method="HEAD",
        )
        assert _quick_validate_remote_csrd_url(url) is False

    def test_prevalidate_logs_failures(self, httpx_mock):
        """When a logs list is provided, failures are recorded in it."""
        url = "https://example.com/gone.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=404,
        )
        logs = []
        result = _quick_validate_remote_csrd_url(url, logs=logs)
        assert result is False
        assert len(logs) > 0
        assert "404" in logs[0]
