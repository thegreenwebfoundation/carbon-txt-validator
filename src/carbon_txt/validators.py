import logging
from pathlib import Path

import rich

from . import exceptions, finders, parsers_toml, schemas

file_finder = finders.FileFinder()
parser = parsers_toml.CarbonTxtParser()

logger = logging.getLogger(__name__)


class CarbonTxtValidator:
    """
    The core class repsonsible for exposing essentially the same functionality to
    the package's API and CLI.interfaces.
    """

    # we main a list of events that happen during validation, process so we can
    # expose them to a user for debugging
    event_log: list = []

    def validate_contents(self, url: str) -> schemas.CarbonTxtFile:
        """
        Validate the provided contents of a carbon.txt file. Returns a CarbonTxtFile object,
        or raises a list of validation exceptions if the contents are invalid.
        """
        pass

    def validate_url(self, url: str) -> schemas.CarbonTxtFile:
        """
        Validate a carbon.txt file at a given URL.
        """
        try:
            result = file_finder.resolve_uri(url)
            parsed_result = parser.fetch_parsed_carbon_txt_file(result)

        # the file path is local, but we can't access it
        except FileNotFoundError:
            full_file_path = Path(url).absolute()
            rich.print(f"No valid carbon.txt file found at {full_file_path}. \n")

        # the file path is remote, and we can't access it
        except exceptions.UnreachableCarbonTxtFile as e:
            logger.error(f"Error: {e}")

        # the file path is reachable, and but it's not valid TOML
        except exceptions.NotParseableTOML as e:
            rich.print(
                f"A carbon.txt file was found at {url}: but it wasn't parseable TOML. Error was: {e}"
            )

        except Exception as e:
            rich.print(f"An unexpected error occurred: {e}")

        validation_results = parser.validate_as_carbon_txt(parsed_result)
        return {"result": validation_results, "logs": [], "exceptions": []}

    def validate_domain(self, domain: str) -> dict:
        """
        Validate a carbon.txt file at a given domain.
        Returns a dictionary containing the CarbonTxtFile,
        a list of logs, and a list of exceptions.
        """
        self.event_log = []  # Reset event log for each validation
        exceptions = []

        try:
            result = file_finder.resolve_domain(domain, logs=self.event_log)
            content = parser.get_carbon_txt_file(result, logs=self.event_log)
            parsed_result = parser.parse_toml(content, logs=self.event_log)
            validation_results = parser.validate_as_carbon_txt(
                parsed_result, logs=self.event_log
            )
        except Exception as ex:
            exceptions.append(ex)
            validation_results = None

        return {
            "result": validation_results,
            "logs": self.event_log,
            "exceptions": exceptions,
        }
