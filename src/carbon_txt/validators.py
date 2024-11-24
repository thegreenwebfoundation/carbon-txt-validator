import logging
from dataclasses import dataclass


import pathlib
import httpx
from typing import Optional, Union
from . import exceptions, finders, parsers_toml, schemas  # noqa
import pydantic
import pydantic_core

file_finder = finders.FileFinder()
parser = parsers_toml.CarbonTxtParser()

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    result: Optional[schemas.CarbonTxtFile]
    logs: list
    exceptions: list


class CarbonTxtValidator:
    """
    The core class repsonsible for exposing essentially the same functionality to
    the package's API and CLI.interfaces.
    """

    # we maintain a list of events that happen during validation, so we can
    # expose them to a user for debugging
    event_log: list = []

    def validate_contents(self, contents: str) -> ValidationResult:
        """
        Validate the provided contents of a carbon.txt file. Returns a CarbonTxtFile object,
        or raises a list of validation exceptions if the contents are invalid.
        """
        self.event_log = []  # Reset event log for each validation

        errors: list[Union[Exception, pydantic_core.ErrorDetails, dict]] = []

        try:
            parsed_result = parser.parse_toml(contents, logs=self.event_log)
            validation_results = parser.validate_as_carbon_txt(
                parsed_result, logs=self.event_log
            )
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
        except pydantic.ValidationError as ex:
            errors.append(*ex.errors())
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
        except Exception as ex:
            errors.append(ex)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate a carbon.txt file at a given URL.
        """
        errors: list[Union[Exception, pydantic_core.ErrorDetails, dict]] = []

        try:
            result = file_finder.resolve_uri(url, logs=self.event_log)
            fetched_file_contents = file_finder.fetch_carbon_txt_file(
                result, logs=self.event_log
            )
            parsed_result = parser.parse_toml(
                fetched_file_contents, logs=self.event_log
            )
            validation_results = parser.validate_as_carbon_txt(
                parsed_result, logs=self.event_log
            )
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # # the file path is local, but we can't access it
        except FileNotFoundError as ex:
            full_file_path = pathlib.Path(url).absolute()
            message = f"No valid carbon.txt file found at {full_file_path}. \n"
            validation_results = None
            self.event_log.append(message)
            errors.append(ex)
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # we have a valid TOML file, but it's not a valid carbon.txt file
        except pydantic.ValidationError as ex:
            message = f"Validation error: {ex}"
            logger.warning(message)
            errors.append(*ex.errors())
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # the file path is remote, and we can't access it
        except exceptions.UnreachableCarbonTxtFile as ex:
            # logger.error(f"Error: {ex}")
            errors.append(ex)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # # the file path is reachable, and but it's not valid TOML. We re-raise the exception
        # with the url listed in the error message, so it's clear to what URL the error refers to
        except exceptions.NotParseableTOML as ex:
            message = f"A file was found at {url}: but it wasn't parseable TOML. Error was: {ex}"
            logger.warning(message)
            self.event_log.append(message)

            errors.append(ex)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # the file path is reachable, but the server returned a 404
        except httpx.HTTPStatusError as ex:
            message = f"An error occurred while fetching the carbon.txt file at {url}."
            logger.warning(message)
            self.event_log.append(message)
            errors.append(ex)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        except Exception as ex:
            message = f"An unexpected error occurred: {ex}"
            logger.warning(message)
            self.event_log.append(message)
            errors.append(ex)
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

    def validate_domain(self, domain: str) -> ValidationResult:
        """
        Validate a carbon.txt file at a given domain.
        Returns a dictionary containing the CarbonTxtFile,
        a list of logs, and a list of exceptions.
        """
        self.event_log = []  # Reset event log for each validation
        errors: list[Union[Exception, pydantic_core.ErrorDetails, dict]] = []

        try:
            result = file_finder.resolve_domain(domain, logs=self.event_log)
            fetched_file_contents = file_finder.fetch_carbon_txt_file(
                result, logs=self.event_log
            )
            parsed_toml = parser.parse_toml(fetched_file_contents, logs=self.event_log)
            validation_results = parser.validate_as_carbon_txt(
                parsed_toml, logs=self.event_log
            )
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
        except Exception as ex:
            errors.append(ex)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
