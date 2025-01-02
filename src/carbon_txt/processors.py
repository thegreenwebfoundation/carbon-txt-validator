import datetime
from arelle import (  # type: ignore
    ModelXbrl,
)
from arelle.api.Session import Session  # type: ignore
from arelle.RuntimeOptions import RuntimeOptions  # type: ignore
from pydantic import BaseModel

import typing


class NoMatchingDatapointsError(ValueError):
    """
    Thrown when a report does not have the expected datapoint.

    This could be because a data point is either
    1. missing, or
    2. intentionallty omitted because it was deemed immaterial
    """


class DataPoint(BaseModel):
    """
    Datapoints are the values that are extracted from the CSRD report, that
    broadly correspond to "supporting evidence" used when registering providers
    with the Green Web Foundation, and credentials in the carbon txt schema.
    """

    name: str
    value: str | float | int
    unit: str  # the type of unit the value is expressed in
    context: str  # the line in the original xml file this value is from
    start_date: datetime.date
    end_date: datetime.date


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
        Read a CSRD report from a URL, and return the parsed report as an object
        """
        return self.xbrls

    def _get_datapoints_for_datapoint_code(
        self, datapoint_code: str
    ) -> list[DataPoint]:
        """
        Get the values for a specific datapoint code from the report
        """
        datapoints = []
        try:
            res = self.xbrls[0].factsByLocalName.get(datapoint_code)

            if not res:
                raise NoMatchingDatapointsError(
                    f"Could not find datapoint with code {datapoint_code}, for report {self.report_url}"
                )

            for item in res:
                readable_label = item.propertyView[2][1]
                # we convert endDatetime and startDatetime to date
                # even though there is a shorter endDate property. this is
                # because endDate is handled differently to both datetimes
                start_date = item.context.startDatetime.date()
                end_date = item.context.endDatetime.date()
                document_line_reference = (
                    f"item.modelDocument.basename - {item.sourceline}"
                )
                qname = str(item.qname)
                value = item.value

                unit = ""
                if "Percentage" in qname:
                    unit = "percentage"
                    value = float(item.value)

                dp = DataPoint(
                    name=readable_label,
                    value=value,
                    unit=unit,
                    context=document_line_reference,
                    start_date=start_date,
                    end_date=end_date,
                )
                datapoints.append(dp)
        except KeyError:
            raise NoMatchingDatapointsError(
                f"Could not find datapoint with code {datapoint_code}"
            )

        return datapoints

    def get_esrs_datapoint_values(
        self, datapoint_codes: typing.List[str]
    ) -> typing.Dict[str, list[DataPoint] | list[NoMatchingDatapointsError]]:
        """
        Accept a list of datapoint codes, and return the values for those datapoints as dict
        containing list of DataPoint objects, keyed by the datapoint code, or a list containing
        the error if the datapoint is not found.
        """
        # redefining the types here to make the mypy happy
        # TODO: see why mypy complains, as we've already defined the return value in
        # method signature
        datapoints_by_code: dict[
            str, list[DataPoint] | list[NoMatchingDatapointsError]
        ] = {}
        for datapoint_code in datapoint_codes:
            try:
                datapoints = self._get_datapoints_for_datapoint_code(datapoint_code)
                datapoints_by_code[datapoint_code] = datapoints
            except NoMatchingDatapointsError as ex:
                datapoints_by_code[datapoint_code] = [ex]

        return datapoints_by_code
