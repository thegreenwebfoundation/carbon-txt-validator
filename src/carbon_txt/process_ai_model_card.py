from .hookspecs import hookimpl
from .http_client import HTTPClient
from .processors import GreenwebAIModelCardProcessor
from .schemas.version_0_5 import Disclosure
import logging
from typing import Optional


from structlog import get_logger

logger = get_logger()


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


plugin_name = "ai-model-card_greenweb"


@hookimpl
def process_document(
    document: Disclosure, logs: Optional[list], http_client: Optional[HTTPClient] = None
):
    """
    Listen for documents linked in the carbon.txt file that are AI Model Cards,
    and parse out any carbon emissions info from the yaml frontmatter
    """
    log_safely(
        f"{plugin_name}: Processing supporting document: {document.url} for {document.domain}",
        logs=logs,
    )
    if document.doc_type == "ai-model-card":
        log_safely(
            f"{__name__}: AI model card found. Processing document: {document}",
            logs=logs,
        )
        try:
            if http_client is None:
                http_client = HTTPClient()
            processor = GreenwebAIModelCardProcessor(
                card_url=document.url, http_client=http_client, logs=logs
            )
            results = processor.get_co2_eq_emissions()
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
