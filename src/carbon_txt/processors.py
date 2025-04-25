import datetime
from arelle import (  # type: ignore
    ModelXbrl,
)
from arelle.api.Session import Session  # type: ignore
from arelle.RuntimeOptions import RuntimeOptions  # type: ignore
from pydantic import BaseModel

import typing
from .exceptions import NoMatchingDatapointsError, NoLoadableCSRDFile

import structlog

logger = structlog.getLogger(__name__)


class DataPoint(BaseModel):
    """
    Datapoints are the values that are extracted from a given CSRD report that
    is linked to in a carbon.txt file.
    A single report or document can contain multiple datapoints, each with a unique code
    that corresponds to a specific value in the ESRS taxonomy.
    """

    name: str
    short_code: str
    value: str | float | int
    unit: str  # the type of unit the value is expressed in
    context: str  # the line in the original xml file this value is from
    file: str  # the URL to the file this value is from
    start_date: datetime.date
    end_date: datetime.date


class ArelleProcessor:
    """
    A processor for reading and parsing CSRD report documents.

    This is a wrapper around the Arelle Library to provide a simpler interface exposing
    only the functionality we need.

    It can be used directly to parse a report, and service queries for specific datapoints,
    but it's designed to be wrapped by other objects that might consume its simplified API as plugins.

    See the GreenwebCSRDProcessor as an exmaple of a class consumign this object's API in a CSRD plugin.
    """

    report_url: str
    xbrls: list[ModelXbrl.ModelXbrl]

    def __init__(self, report_url: str) -> None:
        """
        Initialize the Arelle Processor loading the report from the given URL.

        This begin a session with Arelle, providing an object that will accept
        other objects querying the parsed report for data.

        Args:
            report_url (str): The URL of the report to process

        """

        self.report_url = report_url

        options = RuntimeOptions(
            entrypointFile=str(report_url),
            # TODO it's not clear how to get the output from the logger to only log to
            # the handler. We ideally want to ONLY log to the handler, but there always seems to be
            # output logged to stdout, even if we pass in a null handler.
            # the only option we seem to have is to set the log level
            logLevel="ERROR",
            logFile="logToBuffer",
            # we need to keep the file open to fetch data from the xml
            # file later, when we call various method on the object
            # TODO: does file close when this object is garbage collected?
            keepOpen=True,
        )

        with Session() as session:
            session.run(options)
            self.xbrls = session.get_models()
            if "FileNotLoadable" in self.xbrls[0].errors:
                raise NoLoadableCSRDFile(
                    f"Could not load the file at {self.report_url} as a CSRD report"
                )
            session.close()

    def parsed_reports(self) -> list[ModelXbrl.ModelXbrl]:
        """
        Return the parsed reports from the Arelle session. for querying.

        Returns:
            list[ModelXbrl.ModelXbrl]: A list of parsed reports from the Arelle session.

        """
        return self.xbrls

    def _get_datapoints_for_datapoint_code(
        self, datapoint_code: str, esrs_datapoints: dict[str, str]
    ) -> list[DataPoint]:
        """
        Get the values for a specific datapoint code from the report.

        Args:
            datapoint_code (str): The code of the datapoint to retrieve.
            esrs_datapoints (dict[str, str]): A dictionary of ESRS datapoints to retrieve.
            We have this dictionary to provide a control over the human readable labels
            for the datapoint. This allows for overriding labels for specific data
            points to provide more accessible copy than the defaults in the ESRS taxonomy.
        """
        datapoints = []
        try:
            res = self.xbrls[0].factsByLocalName.get(datapoint_code)
            datapoint_readable_label = esrs_datapoints.get(
                f"esrs:{datapoint_code}", "No label found"
            )
            if not res:
                raise NoMatchingDatapointsError(
                    f"Could not find datapoint with code {datapoint_code}, for report {self.report_url}",
                    datapoint_short_code=datapoint_code,
                    datapoint_readable_label=datapoint_readable_label,
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
                    short_code=datapoint_code,
                    value=value,
                    unit=unit,
                    context=document_line_reference,
                    file=self.report_url,
                    start_date=start_date,
                    end_date=end_date,
                )
                datapoints.append(dp)
        except KeyError:
            raise NoMatchingDatapointsError(
                f"Could not find datapoint with code {datapoint_code}",
                datapoint_short_code=datapoint_code,
                datapoint_readable_label=datapoint_readable_label,
            )

        return datapoints


@typing.runtime_checkable
class CSRDProcessorProtocol(typing.Protocol):
    """
    Our protocol for any CSRD processing plugin should conform to.

    We use this and composition using the ArelleProcessor as an
    alternative to relying on inheritance.
    """

    esrs_datapoints: dict[str, str]

    def get_esrs_datapoint_values(
        self, datapoint_codes: list[str]
    ) -> list[DataPoint | NoMatchingDatapointsError]:
        raise NotImplementedError


class GreenwebCSRDProcessor:
    """

    The class to use for querying CSRD reports, and extracting the data points.

    Internally it uses the ArelleProcessor for querying XBRL data in CSRD reports, and the desired
    kinds of data to look for (i.e. the datapoints in the ESRS we care about), are enumerated in `esrs_datapoints`.
    """

    report_url: typing.Optional[str] = None
    arelle_processor: typing.Optional[ArelleProcessor] = None
    esrs_datapoints: dict[str, str] = {
        "esrs:PercentageOfRenewableSourcesInTotalEnergyConsumption": "E1-5 AR 34 Percentage of renewable sources in total energy consumption",
        "esrs:PercentageOfEnergyConsumptionFromNuclearSourcesInTotalEnergyConsumption": "E1-5 AR 34 Percentage of nuclear in total energy consumption",
        "esrs:EnergyConsumptionRelatedToOwnOperations": "E1-5 37 Total energy consumption related to own operations",
        "esrs:EnergyConsumptionFromFossilSources": "E1-5 37 a - Total energy consumption from fossil sources",
        "esrs:EnergyConsumptionFromNuclearSources": "E1-5 37 b - Total energy consumption from nuclear sources",
        "esrs:EnergyConsumptionFromRenewableSources": "E1-5 37 c - Total energy consumption from renewable sources",
        # "esrs:EnergyConsumptionFromRenewableSources": "E1-5 37 c i - Fuel consumption from renewable sources",
        "esrs:ConsumptionOfPurchasedOrAcquiredElectricityHeatSteamAndCoolingFromRenewableSources": "E1-5 37 c ii Consumption of purchased or acquired electricity, heat, steam, and cooling from renewable sources",
        "esrs:ConsumptionOfSelfgeneratedNonfuelRenewableEnergy": "E1-5 37 c iii - Consumption of self-generated non-fuel renewable energy",
    }

    def __init__(
        self,
        report_url: typing.Optional[str] = None,
        arelle_processor: typing.Optional[ArelleProcessor] = None,
    ) -> None:
        """
        Instantiate the GreenwebCSRDProcessor.
        Accepts either

        1. a report url, in which case it instantiates an ArelleProcessor instance to process the report at the given url,
        2. or an ArelleProcessor instance, which has already consumed and parsed a reportm and is ready to service queries.

        """
        if arelle_processor is not None:
            self.arelle_processor = arelle_processor
            return

        if not arelle_processor and report_url:
            processor = ArelleProcessor(report_url)
            self.arelle_processor = processor

    def setup(self, arelle_processor: ArelleProcessor) -> None:
        """
        Set up the GreenwebCSRDProcessor with an instance of ArelleProcessor.
        Used when the GreenwebCSRDProcessor is initialized wihtout a ArellProcessor instance
        or report URL passed in.
        """
        self.arelle_processor = arelle_processor

    @property
    def local_datapoint_codes(self) -> list[str]:
        """
        Return the list of datapoint codes that are available in the ESRS taxonomy,
        without the `esrs:` prefix.
        """
        qualified_names = self.esrs_datapoints.keys()

        return [name.replace("esrs:", "") for name in qualified_names]

    def get_esrs_datapoint_values(
        self, datapoint_codes: typing.List[str]
    ) -> list[DataPoint | NoMatchingDatapointsError]:
        """
        Accept a list of datapoint codes, and return either:
        - a list of Datapoints or
        - a list containing the error if the datapoint is not found.
        """

        if self.arelle_processor is None:
            raise ValueError(
                "The ArelleProcessor has not been set up. Please call setup() first."
            )

        document_results: list[DataPoint | NoMatchingDatapointsError] = []
        for datapoint_code in datapoint_codes:
            try:
                datapoints = self.arelle_processor._get_datapoints_for_datapoint_code(
                    datapoint_code=datapoint_code, esrs_datapoints=self.esrs_datapoints
                )
                document_results.extend(datapoints)
            except NoMatchingDatapointsError as ex:
                document_results.extend([ex])

        return document_results


assert isinstance(GreenwebCSRDProcessor(), CSRDProcessorProtocol)
