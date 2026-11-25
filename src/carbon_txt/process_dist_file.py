import logging

from structlog import get_logger

from .hookspecs import hookimpl
from .http_client import HTTPClient
from .schemas.version_0_6 import Disclosure


logger = get_logger()

def log_safely(log_message: str, logs: list | None, level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)

plugin_name = "dist-file_greenweb"

# Guarded import - the DIST file processor requires the 'dist_file' extra
try:
    from .processors.dist_file import GreenwebDISTFileProcessor
    DIST_FILE_PROCESSOR_AVAILABLE = True
except ImportError:
    GreenwebDISTFileProcessor = None  # type: ignore
    DIST_FILE_PROCESSOR_AVAILABLE = False

@hookimpl
def process_document(
    document: Disclosure, logs: list | None, http_client: HTTPClient | None = None
):
    """
    Listen for documents linked in the carbon.txt file that are AI Model Cards,
    and parse out any carbon emissions info from the yaml frontmatter
    """
    log_safely(
        f"{plugin_name}: Processing supporting document: {document.url} for {document.domain}",
        logs=logs,
    )
    if document.doc_type == "measurement-data":
        if not DIST_FILE_PROCESSOR_AVAILABLE:
            log_safely(
                f"{plugin_name}: Disclosure with document type measurement-data found but the 'dist' extra is not installed. "
                f"Install it with: uv pip install 'carbon-txt[dist]'",
                logs=logs,
                level=logging.WARNING,
            )
            return {"logs": logs}
        log_safely(
            f"{__name__}: measurement-data file found. Processing document: {document}",
            logs=logs,
        )
        try:
            if http_client is None:
                http_client = HTTPClient()
            processor = GreenwebDISTFileProcessor(
                file_url=document.url, http_client=http_client, logs=logs
            )
            results = processor.get_impacts()
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
