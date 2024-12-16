from arelle import (  # type: ignore
    ModelInstanceObject,
    ModelXbrl,
)
from arelle.api.Session import Session  # type: ignore
from arelle.RuntimeOptions import RuntimeOptions  # type: ignore


class NoMatchingDatapointsError(ValueError):
    """
    Thrown when a report does not have the expected datapoint.

    This could be because a data point is either
    1. missing, or
    2. intentionallty omitted because it was deemed immaterial
    """


class CSRDProcessor:
    """
    A processor for reading and parsing CSRD report documents.
    """

    report_url: str
    xbrls: list[ModelXbrl.ModelXbrl]

    esrs_datapoints: list[str] = [
        "PercentageOfRenewableSourcesInTotalEnergyConsumption",
    ]

    def __init__(self, report_url: str) -> None:
        """
        Initialize the Processor loading the report from the given URL.
        """

        self.report_url = report_url

        options = RuntimeOptions(
            entrypointFile=str(report_url),
            # we need to keep the file open to fetch data from the xml
            # file later, when we call various method on the object
            # TODO: does file close when this object is garbage collected?
            keepOpen=True,
        )

        with Session() as session:
            session.run(options)
            self.xbrls = session.get_models()
            session.close()

    def parsed_reports(self) -> list[ModelXbrl.ModelXbrl]:
        """
        Read a CSRD report from a URL, and return the parsed report as a an object
        """
        return self.xbrls

    def get_esrs_datapoint_values(
        self, datapoint_code: str
    ) -> list[ModelInstanceObject.ModelFact]:
        try:
            res = self.xbrls[0].factsByLocalName.get(datapoint_code)
            if not res:
                raise NoMatchingDatapointsError(
                    f"Could not find datapoint with code {datapoint_code}, for report {self.report_url}"
                )

            return [*res]
        except KeyError:
            raise NoMatchingDatapointsError(
                f"Could not find datapoint with code {datapoint_code}"
            )
