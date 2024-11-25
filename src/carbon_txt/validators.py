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


def log_exception_safely(
    exception: Exception, message: str, errors: list, logs: list, level=logging.WARNING
):  # noqa
    """
    Log an an exception, and append it to a list of errors in a form that can
    be displayed as JSON.
    """
    dumpable_error = f"{type(exception).__name__}: {exception}"
    logger.log(level, message)
    logs.append(message)
    errors.append(dumpable_error)


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
            message = f"Attempting to validate contents of {contents[:40]}"
            self.event_log.append(message)
            parsed_result = parser.parse_toml(contents, logs=self.event_log)
            validation_results = parser.validate_as_carbon_txt(
                parsed_result, logs=self.event_log
            )
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
        except pydantic.ValidationError as ex:
            message = f"Validation error: {ex}"
            self.event_log.append(message)
            errors.append(*ex.errors())
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
        except Exception as ex:
            message = f"An unexpected error occurred: {ex}"
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate a carbon.txt file at a given URL.
        """
        self.event_log = []  # Reset event log for each validation
        errors: list[Union[Exception, pydantic_core.ErrorDetails, dict]] = []

        try:
            message = f"Attempting to validate url: {url}"
            self.event_log.append(message)
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
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # we have a valid TOML file, but it's not a valid carbon.txt file
        except pydantic.ValidationError as ex:
            message = f"Validation error: {ex}"
            self.event_log.append(message)
            errors.append(*ex.errors())
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # the file path is remote, and we can't access it
        except exceptions.UnreachableCarbonTxtFile as ex:
            message = f"Could not fetch the carbon.txt file at {url}. Error was: {ex}"
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # # the file path is reachable, and but it's not valid TOML. We re-raise the exception
        # with the url listed in the error message, so it's clear to what URL the error refers to
        except exceptions.NotParseableTOML as ex:
            message = f"A file was found at {url}: but it wasn't parseable TOML. Error was: {ex}"
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )

        # the file path is reachable, but the server returned a 404
        except httpx.HTTPStatusError as ex:
            message = f"An error occurred while fetching the carbon.txt file at {url}."
            errors, logs = log_exception_safely(
                ex, message, errors, logs=self.event_log
            )
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=logs, exceptions=errors
            )

        except Exception as ex:
            message = f"An unexpected error occurred: {ex}"
            errors, logs = log_exception_safely(
                ex, message, errors, logs=self.event_log
            )
            validation_results = None
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
            message = f"Attempting to resolve domain: {domain}"
            self.event_log.append(message)
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
            message = f"An unexpected error occurred: {ex}"
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
