import logging
from typing import Optional

from structlog import get_logger

from .hookspecs import hookimpl
from .schemas.common import Disclosure

logger = get_logger()


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


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
    logs: Optional[list],
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
