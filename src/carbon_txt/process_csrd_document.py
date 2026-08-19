import logging
import os
from urllib.parse import urlparse

from structlog import get_logger

from .hookspecs import hookimpl
from .http_client import HTTPClient
from .schemas.common import Disclosure

logger = get_logger()

# File extensions that could plausibly be ESEF iXBRL documents
ESEF_VALID_EXTENSIONS = {".xhtml", ".xbrl", ".xml", ".zip", ".htm", ".html"}

# Content types that could plausibly be ESEF iXBRL documents
ESEF_VALID_CONTENT_TYPES = {
    "xhtml",
    "html",
    "xml",
    "application/zip",
    "application/octet-stream",
}

# Markers that indicate a document is actually iXBRL/XBRL rather than a
# regular HTML page. We check for these in a small snippet of the response
# body to distinguish real iXBRL reports from ordinary web pages that happen
# to be served with content-type text/html.
IXBRL_CONTENT_MARKERS = (
    b"<ix:",
    b"xmlns:ix",
    b"<xbrli:",
    b"xmlns:xbrli",
    b"<xbrl",
    b"<context ",
    b"<unit ",
    b"<xbrldi:",
)

# How many bytes of the response body to fetch for content sniffing.
# iXBRL namespaces and root elements appear very early in the document.
_SNIFF_BYTES = 8192


def log_safely(log_message: str, logs: list | None, level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


def _looks_like_esef_url(url: str) -> bool:
    """
    Quick heuristic: does the URL path suggest it could be an ESEF document?

    This is a zero-cost check that prevents obviously wrong URLs (e.g. PDFs,
    images, CSVs) from being passed to Arelle, which would waste several
    seconds on initialisation before failing.

    Extensionless URLs are allowed through (they might be served with
    correct content types).
    """
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    # Allow extensionless URLs and local files without extensions
    return ext in ESEF_VALID_EXTENSIONS or ext == ""


def _looks_like_ixbrl_content(text: bytes) -> bool:
    """
    Check whether the given raw bytes contain iXBRL/XBRL markers.

    This is a content sniff: we fetch a small portion of the response body
    and look for XBRL root elements or iXBRL inline tags. This distinguishes
    genuine iXBRL reports (which use HTML as a carrier format) from ordinary
    web pages that are served with content-type text/html.

    Args:
        text: A snippet of the response body (first few KB is sufficient).

    Returns:
        True if XBRL/iXBRL markers are found, False otherwise.
    """
    # Normalise to lower-case for case-insensitive matching
    text_lower = text.lower()
    return any(marker in text_lower for marker in IXBRL_CONTENT_MARKERS)


def _quick_validate_remote_csrd_url(
    url: str, http_client: HTTPClient | None = None, logs: list | None = None
) -> bool:
    """
    Lightweight HTTP HEAD check before invoking Arelle.

    Catches unreachable URLs, 404s, and obviously non-XBRL content types
    in ~100-200ms, avoiding the 2+ second cost of Arelle session startup
    for URLs that will certainly fail.

    Only checks remote (http/https) URLs. Local file paths are always
    allowed through.
    """
    if not url.startswith(("http://", "https://")):
        return True  # local files - let Arelle handle them

    if http_client is None:
        http_client = HTTPClient()

    try:
        response = http_client.head(url, follow_redirects=True)
        if response.status_code >= 400:
            log_safely(
                f"CSRD pre-check: URL {url} returned HTTP {response.status_code}",
                logs,
                level=logging.WARNING,
            )
            return False

        content_type = response.headers.get("content-type", "").lower()
        if content_type and not any(
            ct in content_type for ct in ESEF_VALID_CONTENT_TYPES
        ):
            log_safely(
                f"CSRD pre-check: URL {url} has content-type '{content_type}' "
                f"which doesn't look like an ESEF document",
                logs,
                level=logging.WARNING,
            )
            return False

        # Content-type check passed, but text/html is ambiguous — it could be
        # a genuine iXBRL report or an ordinary web page. Fetch a small snippet
        # of the body and check for XBRL/iXBRL markers to distinguish them.
        # This avoids passing regular HTML pages to Arelle, which can crash or
        # hang when it encounters unexpected content like <img> tags.
        try:
            get_response = http_client.get(url, follow_redirects=True)
            if get_response.status_code >= 400:
                log_safely(
                    f"CSRD pre-check: URL {url} returned HTTP "
                    f"{get_response.status_code} on content fetch",
                    logs,
                    level=logging.WARNING,
                )
                return False
            # Only check the first few KB — iXBRL markers appear early
            body_snippet = get_response.content[:_SNIFF_BYTES]
        except Exception as sniff_err:  # noqa
            log_safely(
                f"CSRD pre-check: could not sniff content at {url}: {sniff_err}",
                logs,
                level=logging.WARNING,
            )
            # If we can't sniff, fall back to letting Arelle try (the old
            # behaviour) rather than blocking potentially valid reports.
            return True

        if not _looks_like_ixbrl_content(body_snippet):
            log_safely(
                f"CSRD pre-check: URL {url} was fetched successfully but does "
                f"not contain iXBRL/XBRL content. It appears to be a regular "
                f"web page. Skipping Arelle processing.",
                logs,
                level=logging.WARNING,
            )
            return False

        return True
    except Exception as e:  # noqa
        log_safely(
            f"CSRD pre-check: could not reach {url}: {e}",
            logs,
            level=logging.WARNING,
        )
        return False


plugin_name = "csrd_greenweb"

# Guarded import - the CSRD processor requires the 'csrd' extra
try:
    from .processors.csrd_document import GreenwebCSRDProcessor

    CSRD_PROCESSOR_AVAILABLE = True
except ImportError:
    CSRD_PROCESSOR_AVAILABLE = False
    GreenwebCSRDProcessor = None  # type: ignore


@hookimpl
def process_document(
    document: Disclosure,
    logs: list | None,
    http_client: HTTPClient | None = None,
):
    """
    Listen for documents linked in the carbon.txt file that are iXBRL CSRD reports,
    and use Arelle to parse them for selected datapoints
    """
    log_safely(
        f"{plugin_name}: Processing supporting document: {document.url} for {document.domain}",
        logs=logs,
    )

    if document.doc_type == "csrd-report":
        if not CSRD_PROCESSOR_AVAILABLE:
            log_safely(
                f"{plugin_name}: CSRD Report found but the 'csrd' extra is not installed. "
                f"Install it with: uv pip install 'carbon-txt[csrd]'",
                logs=logs,
                level=logging.WARNING,
            )
            return {"logs": logs}

        log_safely(
            f"{__name__}: CSRD Report found. Processing report with Arelle: {document}",
            logs=logs,
        )

        # Quick extension check - zero cost, catches obviously wrong file types
        if not _looks_like_esef_url(document.url):
            log_safely(
                f"CSRD pre-check: URL {document.url} does not have an ESEF-compatible "
                f"file extension. Skipping Arelle processing.",
                logs=logs,
            )
            return {"logs": logs}

        # Lightweight HTTP pre-validation for remote URLs - avoids ~2s Arelle
        # startup cost for unreachable/wrong URLs
        if not _quick_validate_remote_csrd_url(document.url, http_client, logs):
            log_safely(
                f"CSRD pre-check: URL {document.url} failed pre-validation. "
                f"Skipping Arelle processing.",
                logs=logs,
            )
            return {"logs": logs}

        try:
            processor = GreenwebCSRDProcessor(report_url=document.url)

            chosen_datapoints = processor.local_datapoint_codes

            results = processor.get_esrs_datapoint_values(chosen_datapoints)

            return {
                "plugin_name": plugin_name,
                "document_results": results,
                "logs": logs,
            }
        except Exception as e:  # noqa
            log_safely(
                f"Error occurred when loading report at {document.url}: {e}", logs=logs
            )

    else:
        log_safely(
            f"{__name__}: Document type {document.doc_type} seen. Doing nothing",
            logs=logs,
        )

    return {"logs": logs}
