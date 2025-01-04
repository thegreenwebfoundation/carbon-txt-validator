from carbon_txt.hookspecs import hookimpl  # type: ignore

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


@hookimpl
def process_document(document, parsed_carbon_txt_file, logs):
    # This is just a sample function to demonstrate
    # returning the result of ANY processing of the document

    log_safely(
        f"Test Plugin: Processing supporting document: {document.url}", logs=logs
    )
    document_processing_results = document.__dict__
    carbon_test_file_size = parsed_carbon_txt_file.__dict__

    return {
        document.url: [
            "TEST PLUGIN RETURN VALUES",
            document_processing_results,
            carbon_test_file_size,
        ],
        "logs": logs,
    }
