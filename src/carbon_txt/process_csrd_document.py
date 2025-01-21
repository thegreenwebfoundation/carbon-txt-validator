from .hookspecs import hookimpl
from .schemas import CarbonTxtFile, Disclosure
from .processors import CSRDProcessor
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


plugin_name = "csrd_greenweb"


@hookimpl
def process_document(
    document: Disclosure,
    parsed_carbon_txt_file: Optional[CarbonTxtFile],
    logs: Optional[list],
):
    """
    Listen for documents linked in the carbon.txt file that are ixbrl CSRD reports,
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

        try:
            processor = CSRDProcessor(document.url)

            chosen_datapoints = [
                value.replace("esrs:", "")
                for value in CSRDProcessor.esrs_datapoints.keys()
            ]

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
