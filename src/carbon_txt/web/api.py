import pydantic
from django.conf import settings
from django.http import HttpRequest, HttpResponse  # noqa
from ninja import NinjaAPI, Schema
from structlog import get_logger

from .. import exceptions, finders, schemas, validators  # noqa

file_finder = finders.FileFinder()


logger = get_logger()

# Initialize the NinjaAPI with OpenAPI documentation details
ninja_api = NinjaAPI(
    openapi_extra={
        "info": {
            "termsOfService": "https://thegreenwebfoundation.org/terms/",
        }
    },
    title="Carbon.txt Validator API",
    description="This is the API for validating carbon.txt files. ",
)


class CarbonTextSubmission(Schema):
    """
    Schema for the submission of carbon.txt file contents. We expect a string, containing the contents of the carbon.txt file.
    """

    text_contents: str


class CarbonTextUrlSubmission(Schema):
    """
    Schema for the submission of a URL pointing to a carbon.txt file. We expect an URL pointing to a carbon.txt file, which is downloaded and parsed.
    """

    url: pydantic.HttpUrl


def sanitize_document_results(document_results: dict[str, list]) -> dict[str, list]:
    """
    Sanitize document results by converting NoMatchingDatapointsError
    exceptions to dictionaries, otherwise return each result as is.

    Args:
        document_results (dict): The original document results.

    Returns:
        dict: The sanitized document results.
    """
    sanitized_results: dict[str, list] = {}
    for plugin_name, original_output in document_results.items():
        sanitized_output = []
        for item in original_output:
            # we have to turn this into a dict, otherwise it won't serialise
            # to JSON cleanly
            if isinstance(item, exceptions.NoMatchingDatapointsError):
                sanitized_item = item.__dict__()
                sanitized_item["error"] = "NoMatchingDatapointsError"
                sanitized_output.append(sanitized_item)
            else:
                sanitized_output.append(item)

        sanitized_results[plugin_name] = sanitized_output
    return sanitized_results


@ninja_api.post(
    "/validate/file/",
    description="Accept contents of a carbon.txt file and validate it.",
)
def validate_contents(
    request: HttpRequest, carbon_txt_submission: CarbonTextSubmission
) -> HttpResponse:
    """
    Endpoint to validate the contents of a carbon.txt file.

    Args:
        request: The request object.
        CarbonTextSubmission: The schema containing the text contents of the carbon.txt file.

    Returns:
        dict: A dictionary containing the success status and either the validated data or errors.
    """
    validator = validators.CarbonTxtValidator(
        plugins_dir=settings.CARBON_TXT_PLUGINS_DIR,
        active_plugins=settings.ACTIVE_CARBON_TXT_PLUGINS,
    )

    validation_results = validator.validate_contents(
        carbon_txt_submission.text_contents
    )
    if carbon_txt_file := validation_results.result:
        if validation_results:
            doc_results = sanitize_document_results(
                validation_results.document_results or {}
            )
        # TODO: make sure empty doc_results show as {}, with no keys
        # https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/59
        return {
            "success": True,
            "data": carbon_txt_file,
            "logs": validation_results.logs,
            "document_data": doc_results,
        }  # type: ignore
    else:
        return {
            "success": False,
            "errors": validation_results.exceptions,
            "logs": validation_results.logs,
        }  # type: ignore


@ninja_api.post(
    "/validate/url/", description="Fetch a file at a given URL and validate it."
)
def validate_url(
    request: HttpRequest, carbon_txt_url_data: CarbonTextUrlSubmission
) -> HttpResponse:
    """
    Endpoint to validate a carbon.txt file at the provided URL.

    Args:
        request: The request object.
        CarbonTextSubmission: The schema containing the text contents of the carbon.txt file.

    Returns:
        dict: A dictionary containing the success status and either the validated data or errors.
    """
    url_string = str(carbon_txt_url_data.url)
    validator = validators.CarbonTxtValidator(
        plugins_dir=settings.CARBON_TXT_PLUGINS_DIR,
        active_plugins=settings.ACTIVE_CARBON_TXT_PLUGINS,
    )

    validation_results = validator.validate_url(str(url_string))
    if carbon_txt_file := validation_results.result:
        if validation_results:
            doc_results = sanitize_document_results(
                validation_results.document_results or {}
            )
        # TODO: make sure empty doc_results show as {}, with no keys
        # https://github.com/thegreenwebfoundation/carbon-txt-validator/issues/59
        return {
            "success": True,
            "data": carbon_txt_file,
            "document_data": doc_results,
            "logs": validation_results.logs,
        }  # type: ignore
    else:
        return {
            "success": False,
            "errors": validation_results.exceptions,
            "logs": validation_results.logs,
        }  # type: ignore


@ninja_api.get(
    "/json_schema/",
    summary="Retrieve JSON Schema",
    description="Get the JSON schema representation of carbon.txt file spec for validation",
)
def get_json_schema(request: HttpRequest) -> HttpResponse:
    """
    Endpoint to get the JSON schema for a carbon.txt file.
    """
    # Get the JSON schema for a carbon.txt file
    schema = schemas.CarbonTxtFile.model_json_schema()

    return schema  # type: ignore
