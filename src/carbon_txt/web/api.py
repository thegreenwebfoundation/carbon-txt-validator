from ninja import NinjaAPI, Schema
from django.http import HttpRequest, HttpResponse

from carbon_txt.parsers_toml import CarbonTxtParser
from carbon_txt.schemas import CarbonTxtFile
from pydantic import HttpUrl

from .. import finders
from .. import exceptions
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


class CarbonTextSubmission(Schema):
    """
    Schema for the submission of carbon.txt file contents. We expect a string, containing the contents of the carbon.txt file.
    """

    text_contents: str


class CarbonTextUrlSubmission(Schema):
    """
    Schema for the submission of a URL pointing to a carbon.txt file. We expect an URL pointing to a carbon.txt file, which is downloaded and parsed.
    """

    url: HttpUrl


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
    # Initialize the parser
    parser = CarbonTxtParser()

    # Parse the TOML contents from the submission
    parsed = parser.parse_toml(carbon_txt_submission.text_contents)

    # Validate the parsed contents as a carbon.txt file
    result = parser.validate_as_carbon_txt(parsed)

    # Check if the result is a valid CarbonTxtFile instance
    if isinstance(result, CarbonTxtFile):
        return {"success": True, "data": result}

    # Return errors if validation failed
    return {"success": False, "errors": result.errors()}


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
    # Initialize the parser
    parser = CarbonTxtParser()

    # Fetch and parse the contents of the URL
    url_string = str(carbon_txt_url_data.url)
    try:
        result = file_finder.resolve_uri(url_string)
        parsed_result = parser.fetch_parsed_carbon_txt_file(result)
    except exceptions.UnreachableCarbonTxtFile as e:
        err_class = type(e).__name__
        error_message = f"Error: {e}"
        logger.warning(error_message)
        return {"success": False, "errors": [{err_class: error_message}]}

    except exceptions.NotParseableTOML as e:
        err_class = type(e).__name__
        error_message = f"A carbon.txt file was found at {url_string}: but it wasn't parseable TOML. Error was: {e}"
        logger.warning(error_message)
        return {"success": False, "errors": [{err_class: error_message}]}

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        err_class = type(e).__name__
        logger.warning(error_message)
        return {"success": False, "errors": [{err_class: error_message}]}

    # Validate the parsed contents as a carbon.txt file
    validation_results = parser.validate_as_carbon_txt(parsed_result)
    # Check if the result is a valid CarbonTxtFile instance
    if isinstance(validation_results, CarbonTxtFile):
        return {"success": True, "data": validation_results}

    # Return errors if validation failed
    return {"success": False, "errors": validation_results.errors()}


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
    schema = CarbonTxtFile.model_json_schema()

    return schema
