import logging
from typing import Callable, Optional

import frontmatter
from mistletoe import Document
from mistletoe.block_token import Heading
from pydantic import BaseModel
from structlog import get_logger

from ..exceptions import NoMatchingDatapointsError
from ..http_client import HTTPClient


logger = get_logger()


def log_safely(log_message: str, logs: Optional[list], level=logging.INFO):
    """
    Log a message, and append it to a list of logs
    """
    logger.log(level, log_message)
    if logs is not None:
        logs.append(log_message)


class DataPoint(BaseModel):
    """
    A single field of a parsed AI model card.
    """

    short_code: str
    name: str
    unit: str | None
    value: str | float
    file: str


class FieldSpec(BaseModel):
    """
    A field in the AI model card schema. It has
    - a short code (the YAML key)
    - a callable formatter which will parse the value from a string
    - a longer descriptive name
    - and an optional unit
    """

    short_code: str
    format: Callable
    name: str
    unit: str | None


type AIModelCardResponse = DataPoint | NoMatchingDatapointsError


class GreenwebAIModelCardProcessor:
    """
    This class parses co2_eq_emissions data from an AI model card.
    See https://huggingface.co/docs/hub/model-cards-co2 for the expected data format.
    It will return any co2_eq_emissions fields found which are part of the spec,
    and will silently ignore any extra fields. Missing fields will be surfaced
    with an error message.
    """

    FIELDS = [
        FieldSpec(
            short_code="emissions",
            format=float,
            name="CO2 equivalent emissions.",
            unit="grams",
        ),
        FieldSpec(
            short_code="source",
            format=str,
            name="The source of the information, either directly from AutoTrain, code carbon or from a scientific article documenting the model.",
            unit=None,
        ),
        FieldSpec(
            short_code="training_type",
            format=str,
            name="Pre-training or fine-tuning.",
            unit=None,
        ),
        FieldSpec(
            short_code="geographical_location",
            format=str,
            name="The geographical location where the training was carried out",
            unit=None,
        ),
        FieldSpec(
            short_code="hardware_used",
            format=str,
            name="How much compute was used, and what kind.",
            unit=None,
        ),
    ]

    def __init__(
        self,
        card_url: str,
        logs: Optional[list[str]] = None,
        http_client: Optional[HTTPClient] = None,
    ):
        if http_client is None:
            http_client = HTTPClient()

        self.http_client = http_client
        self.card_url = card_url
        self.logs = logs

    def _error_on_all_fields(self, message: str) -> list[NoMatchingDatapointsError]:
        """
        Private helper method to mark all expected fields with the same error message.
        """
        errors = []
        for field in GreenwebAIModelCardProcessor.FIELDS:
            errors.append(
                NoMatchingDatapointsError(
                    datapoint_short_code=field.short_code,
                    datapoint_readable_label=field.name,
                    message=message,
                )
            )
        return errors

    def get_co2_eq_emissions(self) -> list[AIModelCardResponse]:
        """
        Fetch and parse the co2 equivalent emissions data from the AI Model card.
        """
        response = self.http_client.get(self.card_url)
        datapoints: list[AIModelCardResponse] = []
        response.raise_for_status()
        text = response.text
        data = frontmatter.loads(text)
        name = self.get_h1_from_markdown(text)
        if name:
            datapoints.append(
                DataPoint(
                    short_code="name",
                    name="Model name",
                    value=name,
                    file=self.card_url,
                    unit=None,
                )
            )
        try:
            if "co2_eq_emissions" in data:
                # The frontmatter has the co2_eq_emissions section
                co2_data = data["co2_eq_emissions"]
                for field in GreenwebAIModelCardProcessor.FIELDS:
                    if value := co2_data.get(field.short_code):
                        # The given field exists in the emissions data.
                        log_safely(
                            f"Found {field.short_code} in model card with url {self.card_url}",
                            self.logs,
                        )
                        datapoints.append(
                            DataPoint(
                                short_code=field.short_code,
                                name=field.name,
                                unit=field.unit,
                                value=field.format(value),
                                file=self.card_url,
                            )
                        )
                    else:
                        # The given field does not exist in the emissions data
                        log_safely(
                            f"Field {field.short_code} not found in model card with url {self.card_url}",
                            self.logs,
                        )
                        datapoints.append(
                            NoMatchingDatapointsError(
                                datapoint_readable_label=field.name,
                                datapoint_short_code=field.short_code,
                                message=f"This AI model card does not include the {field.short_code} field.",
                            )
                        )

                extra_fields = co2_data.keys() - [
                    f.short_code for f in GreenwebAIModelCardProcessor.FIELDS
                ]
                if len(extra_fields) > 0:
                    log_safely(
                        f"Model card with url {self.card_url} contains extra, ignored, co2_eq_emissions fields: {",".join(extra_fields)}",
                        self.logs,
                    )

            else:
                content_type = response.headers.get("content-type")
                if content_type in ("text/markdown", "text/plain"):
                    # The file can be assumed to be a markdown model card, but has no co2_eq_emissions section
                    log_safely(
                        f"The model card at url {self.card_url} has no co2_eq_emissions section",
                        self.logs,
                    )
                    datapoints.extend(
                        self._error_on_all_fields(
                            "This AI model card does not include a co2_eq_emissions section."
                        )
                    )
                else:
                    # The file cannot be assumed to be a markdown model card, and has no co2_eq_emissions section
                    # We use an alternative error message here to ensure users know to link to the markdown source,
                    # Not the rendered huggingface model page.
                    log_safely(
                        f"The document at url {self.card_url} is not a markdown format model card",
                        self.logs,
                    )
                    datapoints.extend(
                        self._error_on_all_fields(
                            "This AI model card is not in markdown format. Please use the URL to the markdown source of the model card."
                        )
                    )
        except AttributeError:
            # The file has a co2_eq_emissions section, but it is not in the correct format (e.g, it just includes a float without an `emissions` key)
            log_safely(
                f"The document at url {self.card_url} has an incorrectly formatted co2_eq_emissions section",
                self.logs,
            )
            datapoints.extend(
                self._error_on_all_fields(
                    "This AI model card has an incorrectly formatted co2_eq_emissions section."
                )
            )
        return datapoints

    def get_h1_from_markdown(self, markdown: str) -> Optional[str]:
        """
        Get the first top level heading from the document.
        Returns None if parsing fails.
        """

        def _recursively_get_text(element):
            # Mistletoe doesn't give us a method to get all the text of a heading,
            # so this helper will do it for us by traversing its children and returning
            # the text of all the leaf nodes.
            if element.children is None or len(element.children) == 0:
                return element.content
            else:
                return "".join(
                    [_recursively_get_text(child) for child in element.children]
                )

        doc = Document(markdown)
        for element in doc.children:
            if isinstance(element, Heading) and element.level == 1:
                return _recursively_get_text(element)

        return None  # If no header is found
