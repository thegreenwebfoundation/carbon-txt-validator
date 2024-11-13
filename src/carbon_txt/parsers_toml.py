import tomllib as toml
from . import schemas
import httpx
import pathlib

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

    def get_carbon_txt_file(self, str) -> str:
        """
        Accept a URI and either fetch the file over HTTP(S), or read the local file.
        Return a string of contents of the remote carbon.txt file, or the local file.
        """
        if str.startswith("http"):
            result = httpx.get(str).text
            return result

        if pathlib.Path(str).exists():
            return pathlib.Path(str).read_text()

    def fetch_parsed_carbon_txt_file(self, uri: str) -> dict:
        """
        Accept a URI and return a parsed TOML object.
        """
        try:
            carbon_txt = self.get_carbon_txt_file(uri)
            logger.info("Carbon.txt file found at {result}.\n")
            parsed = self.parse_toml(carbon_txt)
            logger.info("Carbon.txt file parsed .\n")
            return parsed
        except toml.TOMLDecodeError as e:
            raise exceptions.NotParseableTOML(e)

    def parse_toml(self, str) -> dict:
        """
        Accept a string of TOML and return a dict representing the
        keys and values going into a CarbonTxtFile object.
        """
        try:
            parsed = toml.loads(str)
            return parsed
        except toml.TOMLDecodeError as e:
            raise exceptions.NotParseableTOML(e)

    def validate_as_carbon_txt(self, parsed) -> schemas.CarbonTxtFile:
        """
        Accept a parsed TOML object and return a CarbonTxtFile, validating that
        necessary keys are present and values are of the correct type.
        """
        from pydantic import ValidationError

        try:
            carb_txt_obj = schemas.CarbonTxtFile(**parsed)
            return carb_txt_obj
        except ValidationError as e:
            logger.warning(e)
            return e
