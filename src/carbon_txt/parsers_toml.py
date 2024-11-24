import tomllib as toml
from . import schemas

from . import exceptions


import logging

logger = logging.getLogger(__name__)
# Do not surface warning messages, as we show them at the end anyway.
logger.setLevel(logging.ERROR)


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
            msg = "Carbon.txt file parsed as valid TOML.\n"
            logger.info(msg)
            logs.append(msg)
            return parsed
        except toml.TOMLDecodeError as e:
            logs.append(e)
            raise exceptions.NotParseableTOML(e)

    def validate_as_carbon_txt(self, parsed, logs=None) -> schemas.CarbonTxtFile:
        """
        Accept a parsed TOML object and return a CarbonTxtFile, validating that
        necessary keys are present and values are of the correct type.
        """
        from pydantic import ValidationError

        try:
            carb_txt_obj = schemas.CarbonTxtFile(**parsed)
            msg = "Parsed TOML was recognised as valid Carbon.txt file.\n"
            logs.append(msg)
            return carb_txt_obj
        except ValidationError as ex:
            logs.append(ex)
            logger.warning(ex)
            return ex
