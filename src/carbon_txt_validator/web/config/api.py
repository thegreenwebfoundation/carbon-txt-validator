from ninja import NinjaAPI, Schema
from django.http import HttpRequest, HttpResponse

from carbon_txt_validator.parsers_toml import CarbonTxtParser
from carbon_txt_validator.schemas import CarbonTxtFile

# Initialize the NinjaAPI with OpenAPI documentation details
ninja_api = NinjaAPI(
    openapi_extra={
        "info": {
            "termsOfService": "https://thegreenwebfoundation.org/terms/",
        }
    },
    title="Carbon.txt Validator API",
    description="API for validating carbon.txt files.",
)


class CarbonTextSubmission(Schema):
    """
    Schema for the submission of carbon.txt file contents. We use
    """

    text_contents: str


@ninja_api.post(
    "/validate/", description="Accept contents of a carbon.txt file and validate it."
)
def validate_contents(
    request: HttpRequest, CarbonTextSubmission: CarbonTextSubmission
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
    parsed = parser.parse_toml(CarbonTextSubmission.text_contents)

    # Validate the parsed contents as a carbon.txt file
    result = parser.validate_as_carbon_txt(parsed)

    # Check if the result is a valid CarbonTxtFile instance
    if isinstance(result, CarbonTxtFile):
        return {"success": True, "data": result}

    # Return errors if validation failed
    return {"success": False, "errors": result.errors()}
