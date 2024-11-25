from ninja import NinjaAPI, Schema
from django.http import HttpRequest, HttpResponse  # noqa


import pydantic

from .. import finders, validators, schemas, exceptions  # noqa
import logging

file_finder = finders.FileFinder()
logger = logging.getLogger(__name__)

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

validator = validators.CarbonTxtValidator()


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

    validation_results = validator.validate_contents(
        carbon_txt_submission.text_contents
    )
    if carbon_txt_file := validation_results.result:
        return {"success": True, "data": carbon_txt_file}  # type: ignore
    else:
        return {"success": False, "data": validation_results.exceptions}  # type: ignore


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

    validation_results = validator.validate_url(str(url_string))
    if carbon_txt_file := validation_results.result:
        return {"success": True, "data": carbon_txt_file}  # type: ignore
    else:
        return {"success": False, "errors": validation_results.exceptions}  # type: ignore


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
