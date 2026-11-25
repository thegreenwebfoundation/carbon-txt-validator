import datetime
import httpx
import json
import logging

from pydantic import BaseModel
from structlog import get_logger

from ..exceptions import NoMatchingDatapointsError
from ..http_client import HTTPClient

logger = get_logger()

try:
    import jsonschema
    import json_source_map as jsm
    OPTIONAL_DEPENDENCIES_AVAILABLE = True
except ImportError:
    jsonschema = None
    jsm = None
    OPTIONAL_DEPENDENCIES_AVAILABLE = False

class OptionalDependenciesNotInstalledError(ImportError):
    """Raised when the dist optional dependencies are not installed"""

def _require_optional_dependencies():
    """Check the optional dependencies are installed, and if not raise a helpful error message."""
    if not OPTIONAL_DEPENDENCIES_AVAILABLE:
        raise OptionalDependenciesNotInstalledError(
            "The DIST file processor requires the 'dist' extra to be installed. "
            "Install it with: uv pip install 'carbon-txt[dist]'"
        )

def log_safely(log_message: str, logs: list | None, level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


DIST_SCHEMAS_PREFIX="https://dist.greenweb.org/schema/dist/"


class DataPoint(BaseModel):
    name: str
    short_code: str
    value: str | float | int | None
    unit: str
    context: str
    file: str
    start_date: datetime.date
    end_date: datetime.date

class GreenwebDISTFileProcessor:
    def __init__(
        self,
        file_url: str,
        logs: list[str] | None = None,
        http_client: HTTPClient | None = None,
    ):
        _require_optional_dependencies()

        if http_client is None:
            http_client = HTTPClient()

        self.http_client = http_client
        self.file_url = file_url
        self.logs = logs

    def get_impacts(self):
        """
        Attempt to parse a file listed as a 'measurement-data' disclosure as a DIST file (https://dist.greenweb.org).
        This will fetch the file, ensure that it references a valid DIST schema and validates against it, and extract
        measurements for the 'carbon' impact dimension, if present, as datapoints.
        """

        impacts : list[DataPoint | NoMatchingDatapointsError] = []

        # Fetch and parse the DIST file.
        try:
            response = self.http_client.get(self.file_url, follow_redirects=True)
            response.raise_for_status()
            dist_json = json.loads(response.text)
            source_map = jsm.calculate(response.text) # type: ignore
        except (httpx.ConnectError, httpx.HTTPStatusError, json.JSONDecodeError) as e:
            # The file is not reachable, or is not in JSON format.
            log_safely(
                f"Could not parse document at {self.file_url} as a DIST file: {type(e).__name__} - {e}",
                self.logs,
            )
            return impacts


        # Fetch and parse the referenced schema.
        schema_url = dist_json.get("$schema")
        if not schema_url or not schema_url.startswith(DIST_SCHEMAS_PREFIX):
            #The file is JSON but either does not reference a schema, or references a schema that is not an official DIST schema.

            log_safely(
                f"Could not parse document at {self.file_url} as a DIST file: File is valid JSON, but $schema does not reference a valid DIST schema.",
                self.logs,
            )
            return impacts
        try:
            response = self.http_client.get(schema_url, follow_redirects=True)
            response.raise_for_status()
            schema = response.json()
        except (httpx.ConnectError, httpx.HTTPStatusError, json.JSONDecodeError) as e:
            # The schema file is not reachable, or is not in JSON format.
            log_safely(
                f"Could not parse document at {self.file_url} as a DIST file - Error while retrieving referenced schema: {type(e).__name__} - {e}",
                self.logs,
            )
            return impacts


        # Validate the json data agains the referenced schema.
        try:
            jsonschema.validate(dist_json, schema) # type: ignore
        except jsonschema.ValidationError as e: #type: ignore
            # The JSON data does not validate against the referenced schema.
            log_safely(
                f"Could not parse document at {self.file_url} as a DIST file - File does not conform to DIST schema: {e}",
                self.logs,
            )
            return impacts

        # Extract the relevant data from the json file.
        period_from = datetime.date.fromisoformat(dist_json["report"]["reporting_period"]["from"])
        period_to = datetime.date.fromisoformat(dist_json["report"]["reporting_period"]["to"])
        if "carbon" not in dist_json["report"]["impacts"]:
            # The file is a valid DIST file, but does not include the carbon dimension.
            log_safely(
                f"Could not retrieve carbon emissions from DIST file at {self.file_url}: Reported impacts do not include the 'carbon' dimension.",
                self.logs,
            )
            return impacts
        for (index, impact) in enumerate(dist_json["report"]["impacts"]["carbon"]):
            pointer = f"/report/impacts/carbon/{index}"
            source_map_entry = source_map[pointer]
            categories = ", ".join(impact["categories"])
            if impact["value"] is not None:
                # The impact value is not "null" - this is a measured or estimated impact.
                result = DataPoint(
                    file=self.file_url,
                    context=f"{pointer} (line: {source_map_entry.value_start.line + 1})",
                    name = categories,
                    short_code = categories,
                    start_date= period_from,
                    end_date= period_to,
                    value = impact["value"],
                    unit = impact["unit"],
                )
            else:
                # The impact value is null - this is reported as an unmeasured value, and we include the notes field if present for explanation.
                result = NoMatchingDatapointsError(
                    datapoint_short_code = categories,
                    datapoint_readable_label=categories,
                    message = impact.get("notes", "-")
                )
            impacts.append(result)
        return impacts


