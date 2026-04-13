import datetime
from collections import defaultdict

from arelle import (  # type: ignore
    ModelXbrl,
)
from arelle.api.Session import Session  # type: ignore
from arelle.RuntimeOptions import RuntimeOptions  # type: ignore
from pydantic import BaseModel

import typing
from ..exceptions import NoMatchingDatapointsError, NoLoadableCSRDFile

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


class ArelleSessionManager:
    """
    Manages a reusable Arelle Session to avoid the overhead of creating
    a new controller, plugin manager, and logging infrastructure for
    every report loaded.

    Uses skipDTS=True to skip full taxonomy discovery, which cuts load
    time by ~85%. Since we only need to read fact values by local name,
    we build our own index from the parsed facts instead of relying on
    Arelle's factsByLocalName (which requires full DTS).
    """

    def __init__(self) -> None:
        self._session: Session | None = None

    def load_report(self, report_url: str) -> ModelXbrl.ModelXbrl:
        """
        Load an XBRL/iXBRL report and return the parsed model.

        Reuses the underlying Arelle Session across calls, avoiding
        repeated controller and plugin manager initialisation.

        Args:
            report_url: Path or URL to the report file.

        Returns:
            The parsed ModelXbrl for the report.

        Raises:
            NoLoadableCSRDFile: If Arelle cannot load the file.
        """
        if self._session is None:
            self._session = Session()

        options = RuntimeOptions(
            entrypointFile=str(report_url),
            logLevel="ERROR",
            logFile="logToBuffer",
            keepOpen=True,
            # Skip full Discoverable Taxonomy Set loading. We only need
            # to read fact values by local name, so the full taxonomy
            # schema/linkbase traversal is unnecessary. This reduces
            # load time from ~2s to ~0.3s per report.
            skipDTS=True,
        )

        self._session.run(options)
        models = self._session.get_models()

        # get_models() returns all models loaded across runs with keepOpen=True,
        # so the latest model is always the last one
        model = models[-1]

        if "FileNotLoadable" in model.errors:
            raise NoLoadableCSRDFile(
                f"Could not load the file at {report_url} as a CSRD report"
            )

        return model

    def close(self) -> None:
        """Close the Arelle session and release resources."""
        if self._session is not None:
            self._session.close()
            self._session = None


# Module-level shared session manager. Reused across ArelleProcessor
# instances to avoid repeated Arelle controller startup.
_shared_session_manager: ArelleSessionManager | None = None


def get_shared_session_manager() -> ArelleSessionManager:
    """Get or create the shared ArelleSessionManager singleton."""
    global _shared_session_manager
    if _shared_session_manager is None:
        _shared_session_manager = ArelleSessionManager()
    return _shared_session_manager


class ArelleProcessor:
    """
    A processor for reading and parsing CSRD report documents.

    This is a wrapper around the Arelle Library to provide a simpler interface exposing
    only the functionality we need.

    It can be used directly to parse a report, and service queries for specific datapoints,
    but it's designed to be wrapped by other objects that might consume its simplified API as plugins.

    See the GreenwebCSRDProcessor as an example of a class consuming this object's API in a CSRD plugin.
    """

    report_url: str
    _model: ModelXbrl.ModelXbrl
    _facts_by_local_name: dict[str, set]

    def __init__(
        self,
        report_url: str,
        session_manager: ArelleSessionManager | None = None,
    ) -> None:
        """
        Initialize the Arelle Processor loading the report from the given URL.

        Uses a shared ArelleSessionManager by default to reuse the Arelle
        session across multiple report loads, avoiding repeated controller
        and plugin manager initialisation.

        Args:
            report_url: The URL or path of the report to process.
            session_manager: Optional ArelleSessionManager to use. If None,
                uses the shared module-level singleton.
        """
        self.report_url = report_url

        if session_manager is None:
            session_manager = get_shared_session_manager()

        self._model = session_manager.load_report(report_url)

        # Build our own local name index from the parsed facts.
        # With skipDTS=True, Arelle's built-in factsByLocalName is not
        # populated, so we construct an equivalent index here.
        self._facts_by_local_name = defaultdict(set)
        for fact in self._model.facts:
            if hasattr(fact, "qname") and fact.qname is not None:
                self._facts_by_local_name[fact.qname.localName].add(fact)

    @property
    def xbrls(self) -> list[ModelXbrl.ModelXbrl]:
        """Backwards-compatible access to the parsed model as a list."""
        return [self._model]

    def parsed_reports(self) -> list[ModelXbrl.ModelXbrl]:
        """
        Return the parsed reports from the Arelle session for querying.

        Returns:
            list[ModelXbrl.ModelXbrl]: A list of parsed reports from the Arelle session.
        """
        return [self._model]

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
        # Resolve the readable label up front so it's always available for error reporting
        datapoint_readable_label = esrs_datapoints.get(
            f"esrs:{datapoint_code}", "No label found"
        )

        res = self._facts_by_local_name.get(datapoint_code)

        if not res:
            raise NoMatchingDatapointsError(
                f"Could not find datapoint with code {datapoint_code}, for report {self.report_url}",
                datapoint_short_code=datapoint_code,
                datapoint_readable_label=datapoint_readable_label,
            )

        datapoints = []
        for item in res:
            # With skipDTS=True, propertyView[2][1] returns the namespace
            # rather than a human-readable label. We use the label from
            # our own esrs_datapoints dict instead, stripping the ESRS code prefix.
            readable_label = datapoint_readable_label
            # Strip the ESRS reference code prefix (e.g. "E1-5 37 c - ") to get
            # just the descriptive label, matching the taxonomy label format
            parts = readable_label.split(" ", 1)
            if len(parts) > 1:
                # Find where the descriptive text starts (after code like "E1-5 AR 34")
                # by looking for the first letter after the numeric/code part
                for i, ch in enumerate(readable_label):
                    if ch.isalpha() and i > 0 and readable_label[i - 1] == " ":
                        # Check if this looks like part of a code (e.g., "AR", "a", "b", "c")
                        remaining = readable_label[i:]
                        if (
                            remaining[0].isupper()
                            and len(remaining) > 2
                            and remaining[1].islower()
                        ):
                            # This looks like the start of a descriptive phrase
                            readable_label = remaining
                            break

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
