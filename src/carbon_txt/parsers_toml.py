import tomllib as toml
from . import schemas

from . import exceptions
import pydantic
import typing

import logging
from structlog import get_logger

logger = get_logger()

# # Do not surface warning messages, as we show them at the end anyway.


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
            raise exceptions.NotParseableTOML(ex)

    def validate_as_carbon_txt(
        self, parsed, logs=None
    ) -> typing.Optional[schemas.CarbonTxtFile]:
        """
        Accept a parsed TOML object and return a CarbonTxtFile, validating that
        necessary keys are present and values are of the correct type.
        """

        try:
            carb_txt_obj = schemas.CarbonTxtFile(**parsed)
            message = "Parsed TOML was recognised as valid Carbon.txt file.\n"
            logs.append(message)
            return carb_txt_obj
        except pydantic.ValidationError as ex:
            log_safely("Validation failed.", logs, level=logging.WARNING)
            raise ex
