import logging
from dataclasses import dataclass


import pathlib
import httpx
from typing import Optional, Union
from . import exceptions, finders, parsers_toml, schemas  # noqa
from .plugins import pm, module_from_path
import pydantic
import pydantic_core

file_finder = finders.FileFinder()
parser = parsers_toml.CarbonTxtParser()

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    logs: list
    exceptions: list
    result: Optional[schemas.CarbonTxtFile]
    document_results: Optional[list] = None


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

    def __init__(self, plugins_dir: Optional[str] = None):
        """
        Initialise the validator, registering any required plugins in the
        provided plugin directory `plugins_dir`
        """
        if plugins_dir is not None:
            plugins_path = pathlib.Path(plugins_dir).resolve()
            for filepath in plugins_path.glob("*.py"):
                if not filepath.is_file():
                    continue
                mod = module_from_path(str(filepath), name=filepath.name)
                try:
                    pm.register(mod)
                except ValueError:
                    logger.warning(f"Plugin already registered: {mod}")
                    # Plugin already registered
                    pass

    def _append_document_processing(
        self, validation_results: schemas.CarbonTxtFile
    ) -> list:
        supporting_documents = validation_results.org.credentials
        result_list = []

        for supporting_document in supporting_documents:
            result_sub_list = pm.hook.process_document(
                document=supporting_document,
                parsed_carbon_txt_file=validation_results,
                logs=[],
            )

            # we need to append all the logs to the event log so we can show them
            # in the API requests
            for item in result_sub_list:
                if item.get("logs"):
                    hook_logs = item.pop("logs")
                    self.event_log.extend(hook_logs)

        result_list.extend(result_sub_list)
        return result_list

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

            if validation_results:
                result_list = self._append_document_processing(validation_results)

            assert len(result_list) == 1

            return ValidationResult(
                result=validation_results,
                logs=self.event_log,
                exceptions=errors,
                document_results=result_list or [],
            )
        except pydantic.ValidationError as ex:
            message = f"Validation error: {ex}"
            self.event_log.append(message)
            errors.extend(ex.errors())
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

            if validation_results:
                result_list = self._append_document_processing(validation_results)

            return ValidationResult(
                result=validation_results,
                logs=self.event_log,
                exceptions=errors,
                document_results=result_list or [],
            )

        # the file path is local, but we can't access it
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
            errors.extend(ex.errors())
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

        # the file path is reachable, and but it's not valid TOML. We re-raise the exception
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
            log_exception_safely(ex, message, errors, self.event_log)
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

            logger.info("Validation results: %s", validation_results)

            if validation_results:
                result_list = self._append_document_processing(validation_results)

            return ValidationResult(
                result=validation_results,
                logs=self.event_log,
                exceptions=errors,
                document_results=result_list or [],
            )
        except Exception as ex:
            message = f"An unexpected error occurred: {ex}"
            log_exception_safely(ex, message, errors, self.event_log)
            validation_results = None
            return ValidationResult(
                result=validation_results, logs=self.event_log, exceptions=errors
            )
