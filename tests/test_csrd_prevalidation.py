"""Tests for CSRD pre-validation helpers.

These functions provide fast, cheap checks before invoking the expensive
Arelle XBRL processor.
"""

import httpx

from carbon_txt.process_csrd_document import (
    _looks_like_esef_url,
    _looks_like_ixbrl_content,
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
        """A reachable URL with an HTML-family content-type and iXBRL content passes."""
        url = "https://example.com/report.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "text/html"},
        )
        # The content sniff fetches the body via GET — must contain
        # iXBRL markers for validation to pass.
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            headers={"content-type": "text/html"},
            content=b'<?xml version="1.0"?><html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>report</body></html>',
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
        """A 200 with no content-type header is allowed through (if iXBRL content found)."""
        url = "https://example.com/report.xhtml"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            # No content-type header
        )
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            content=b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>report</body></html>',
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


# ---------------------------------------------------------------------------
# _looks_like_ixbrl_content
# ---------------------------------------------------------------------------


class TestLooksLikeIxbrlContent:
    """Content sniffing to distinguish real iXBRL from regular HTML pages."""

    def test_detects_ixbrl_namespace(self):
        """A document with the iXBRL inline namespace is detected as iXBRL."""
        content = b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body>report</body></html>'
        assert _looks_like_ixbrl_content(content) is True

    def test_detects_xbrl_root_element(self):
        """A document starting with an <xbrl> root element is detected as iXBRL."""
        content = b'<?xml version="1.0"?><xbrl xmlns="http://www.xbrl.org/2003/instance"><context id="c1"/></xbrl>'
        assert _looks_like_ixbrl_content(content) is True

    def test_detects_context_element(self):
        """A document with <context> elements is detected as iXBRL."""
        content = b'<xbrli:xbrl><context id="ctx-2024"><entity>...</entity></context></xbrli:xbrl>'
        assert _looks_like_ixbrl_content(content) is True

    def test_rejects_regular_html_page(self):
        """A regular HTML page (no XBRL markers) is not detected as iXBRL."""
        content = (
            b"<!DOCTYPE html><html><head><title>State of the Internet</title></head>"
            b"<body><h1>Report 2026</h1><p>Some content</p>"
            b'<img src="/wp-content/uploads/cover.png" alt="Cover" />'
            b"</body></html>"
        )
        assert _looks_like_ixbrl_content(content) is False

    def test_rejects_wordpress_page_with_img_tags(self):
        """The exact scenario from the bug report: a WP page with img tags."""
        content = (
            b"<!DOCTYPE html><html lang='en'><head>"
            b"<title>State of the Fossil Free Internet 2026</title>"
            b"</head><body><header><nav><a href='/about'>About</a></nav>"
            b'<img src="/wp-content/uploads/2024/01/hero-banner.jpg" alt="Hero" width="1200" />'
            b"</header><main><article><h1>State of the Fossil Free Internet 2026</h1>"
            b'<img src="/wp-content/uploads/2024/01/chart1.png" alt="Chart" />'
            b"</article></main><footer>&copy; 2026</footer></body></html>"
        )
        assert _looks_like_ixbrl_content(content) is False

    def test_case_insensitive(self):
        """XBRL markers are matched case-insensitively."""
        content = b"<IX:NONNUMERIC>value</IX:NONNUMERIC>"
        assert _looks_like_ixbrl_content(content) is True

    def test_empty_content(self):
        """Empty content is not iXBRL."""
        assert _looks_like_ixbrl_content(b"") is False

    def test_only_checks_provided_bytes(self):
        """Only the bytes provided are checked (no additional fetching)."""
        # A real iXBRL document truncated to just the first few bytes
        # before any marker appears should return False
        content = b"<!DOCTYPE html><html><head>"
        assert _looks_like_ixbrl_content(content) is False


# ---------------------------------------------------------------------------
# full pre-validation: regular HTML page at an extensionless URL
# ---------------------------------------------------------------------------


class TestPrevalidationRejectsHtmlPage:
    """The exact bug scenario: a csrd-report URL pointing at a regular HTML page.

    Before the content sniffing fix, an extensionless URL serving text/html
    would pass both the extension check and the content-type check, then get
    passed to Arelle which would choke on the HTML content (e.g. <img> tags).
    """

    def test_extensionless_html_page_is_rejected(self, httpx_mock):
        """An extensionless URL serving a regular HTML page fails pre-validation."""
        url = "https://example.com/publications/state-of-the-fossil-free-internet-2026/"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
        )
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
            content=(
                b"<!DOCTYPE html><html><head><title>State of the Internet</title>"
                b"</head><body><h1>Report 2026</h1>"
                b'<img src="/wp-content/uploads/cover.png" alt="Cover" />'
                b"</body></html>"
            ),
        )
        logs = []
        assert _quick_validate_remote_csrd_url(url, logs=logs) is False
        assert any("does not contain iXBRL" in log for log in logs)

    def test_extensionless_ixbrl_page_is_accepted(self, httpx_mock):
        """An extensionless URL serving genuine iXBRL content passes pre-validation."""
        url = "https://example.com/reports/sustainability-2026/"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
        )
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
            content=(
                b'<?xml version="1.0"?>'
                b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">'
                b"<body><ix:nonNumeric>100</ix:nonNumeric></body></html>"
            ),
        )
        logs = []
        assert _quick_validate_remote_csrd_url(url, logs=logs) is True

    def test_plugin_gracefully_skips_html_page(self, httpx_mock):
        """The full plugin path: a csrd-report at an HTML page URL returns
        gracefully without invoking Arelle (no plugin_name in result)."""
        from carbon_txt.process_csrd_document import process_document
        from carbon_txt.schemas.common import Disclosure

        url = "https://staging.thegreenwebfoundation.org/publications/state-of-the-fossil-free-internet-2026/"
        httpx_mock.add_response(
            url=url,
            method="HEAD",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
        )
        httpx_mock.add_response(
            url=url,
            method="GET",
            status_code=200,
            headers={"content-type": "text/html; charset=UTF-8"},
            content=(
                b"<!DOCTYPE html><html lang='en'><head>"
                b"<title>State of the Fossil Free Internet 2026</title>"
                b"</head><body><header>"
                b'<img src="/wp-content/uploads/2024/01/hero-banner.jpg" alt="Hero" />'
                b"</header><main><article><h1>State of the Fossil Free Internet 2026</h1>"
                b'<img src="/wp-content/uploads/2024/01/chart1.png" alt="Chart" />'
                b"</article></main><footer>&copy; 2026</footer></body></html>"
            ),
        )

        doc = Disclosure(
            doc_type="csrd-report",
            url=url,
            domain="staging.thegreenwebfoundation.org",
        )
        logs = []
        result = process_document(document=doc, logs=logs)

        # Should return early — no Arelle processing, no exception
        assert "plugin_name" not in result
        assert any("does not contain iXBRL" in log for log in logs)
