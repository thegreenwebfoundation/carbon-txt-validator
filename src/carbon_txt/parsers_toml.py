import logging
import typing
import html.parser
import pydantic
import tomllib as toml
from structlog import get_logger

from . import exceptions, schemas

logger = get_logger()

# # Do not surface warning messages, as we show them at the end anyway.


class HTMLValidator(html.parser.HTMLParser):
    """A simple HTML validator that tracks parsing errors."""

    def __init__(self):
        super().__init__()
        self.errors = []

    def error(self, message):
        self.errors.append(message)


def is_valid_html(html_string, logs=None):
    """
    Check if a string is valid parsable HTML. Used to distinguish invalid TOML
    files from valid HTML files that may have been returned by a server
    when a carbon.txt file is expected.

    Args:
        html_string: The string to check
        logs: Optional list to append log messages to

    Returns:
        bool: True if the string is valid HTML, False otherwise
    """
    try:
        parser = HTMLValidator()
        parser.feed(html_string)

        if parser.errors:
            if logs:
                logs.append(f"HTML validation failed: {parser.errors}")
            return False

        log_safely("String parsed as valid HTML.", logs)
        return True

    except Exception as ex:
        log_safely(f"HTML parsing failed: {str(ex)}", logs, level=logging.WARNING)
        return False


def log_safely(log_message: str, logs: typing.Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs:
        logs.append(log_message)


class CarbonTxtParser:
    """
    Responsible for parsing carbon.txt files, checking
    they are valid TOML, and that parsed data structures
    have the expected top level keys and values.
    """

    def parse_toml(self, str, logs=None) -> dict:
        """
        Accept a string of TOML and return a dict representing the
        keys and values going into a CarbonTxtFile object.
        """
        try:
            parsed = toml.loads(str)
            log_safely("Carbon.txt file parsed as valid TOML.", logs)
            return parsed
        except toml.TOMLDecodeError as ex:
            log_safely("TOML parsing failed.", logs, level=logging.WARNING)

            log_safely("Checking if content is an valid HTML page instead.", logs)
            if is_valid_html(str, logs):
                log_safely(
                    "Parsed content is valid HTML, not TOML.",
                    logs,
                    level=logging.WARNING,
                )
                raise exceptions.NotParseableTOMLButHTML(ex)

            raise exceptions.NotParseableTOML(ex)

    def validate_as_carbon_txt(
        self, parsed, logs: typing.Optional[list] = None
    ) -> typing.Optional[schemas.CarbonTxtFile]:
        """
        Accept a parsed TOML object and return a CarbonTxtFile, validating that
        necessary keys are present and values are of the correct type.
        """

        try:
            carb_txt_obj = schemas.CarbonTxtFile(**parsed)
            message = "Parsed TOML was recognised as valid Carbon.txt file.\n"
            log_safely(message, logs)
            return carb_txt_obj
        except pydantic.ValidationError as ex:
            log_safely("Validation failed.", logs, level=logging.WARNING)
            raise ex
