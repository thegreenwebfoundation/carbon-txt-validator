import logging

from structlog import get_logger

from carbon_txt.hookspecs import hookimpl  # type: ignore

logger = get_logger("test_plugin")


plugin_name = "test_plugin"


def log_safely(log_message: str, logs: list | None, level=logging.INFO):
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
    return {
        "plugin_name": plugin_name,
        "document_results": [
            {
                "test_key": "TEST PLUGIN VALUE",
            }
        ],
        "logs": logs,
    }
