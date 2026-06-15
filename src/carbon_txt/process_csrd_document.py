import os
from urllib.parse import urlparse

from .hookspecs import hookimpl
from .http_client import HTTPClient
from .schemas.common import Disclosure
from .processors import GreenwebCSRDProcessor
import logging
from typing import Optional


from structlog import get_logger

logger = get_logger()

# File extensions that could plausibly be ESEF iXBRL documents
ESEF_VALID_EXTENSIONS = {".xhtml", ".xbrl", ".xml", ".zip", ".htm", ".html"}

# Content types that could plausibly be ESEF iXBRL documents
ESEF_VALID_CONTENT_TYPES = {"xhtml", "html", "xml", "application/zip", "application/octet-stream"}


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
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


def _quick_validate_remote_csrd_url(
    url: str, http_client: Optional[HTTPClient] = None, logs: Optional[list] = None
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
        if content_type and not any(ct in content_type for ct in ESEF_VALID_CONTENT_TYPES):
            log_safely(
                f"CSRD pre-check: URL {url} has content-type '{content_type}' "
                f"which doesn't look like an ESEF document",
                logs,
                level=logging.WARNING,
            )
            return False

        return True
    except Exception as e:
        log_safely(
            f"CSRD pre-check: could not reach {url}: {e}",
            logs,
            level=logging.WARNING,
        )
        return False


plugin_name = "csrd_greenweb"


@hookimpl
def process_document(
    document: Disclosure,
    logs: Optional[list],
    http_client: Optional[HTTPClient] = None,
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
        except Exception as e:
            log_safely(
                f"Error occurred when loading report at {document.url}: {e}", logs=logs
            )

    else:
        log_safely(
            f"{__name__}: Document type {document.doc_type} seen. Doing nothing",
            logs=logs,
        )

    return {"logs": logs}
