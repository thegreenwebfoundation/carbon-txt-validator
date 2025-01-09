import datetime
from arelle import (  # type: ignore
    ModelXbrl,
)
from arelle.api.Session import Session  # type: ignore
from arelle.RuntimeOptions import RuntimeOptions  # type: ignore
from pydantic import BaseModel

import typing
from .exceptions import NoMatchingDatapointsError, NoLoadableCSRDFile


class DataPoint(BaseModel):
    """
    Datapoints are the values that are extracted from the CSRD report, that
    broadly correspond to "supporting evidence" used when registering providers
    with the Green Web Foundation, and credentials in the carbon txt schema.
    """

    name: str
    short_code: str
    value: str | float | int
    unit: str  # the type of unit the value is expressed in
    context: str  # the line in the original xml file this value is from
    file: str  # the url to the file this value is from
    start_date: datetime.date
    end_date: datetime.date


class CSRDProcessor:
    """
    A processor for reading and parsing CSRD report documents.
    """

    report_url: str
    xbrls: list[ModelXbrl.ModelXbrl]

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
    # these data points are ones we might look for too
    # "esrs:PercentageOfContractualInstrumentsUsedForSaleAndPurchaseOfUnbundledEnergyAttributeClaimsInRelationToScope2GHGEmissions",
    # "esrs:PercentageOfContractualInstrumentsUsedForSaleAndPurchaseOfEnergyBundledWithAttributesAboutEnergyGenerationInRelationToScope2GHGEmissions",
    # "esrs:DisclosureOfEnergyConsumptionAndMixExplanatory",
    # "esrs:DisclosureOfTypesOfContractualInstrumentsUsedForSaleAndPurchaseOfEnergyBundledWithAttributesAboutEnergyGenerationOrForUnbundledEnergyAttributeClaimsExplanatory",
    # "esrs:RenewableEnergyProduction",

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
            if "FileNotLoadable" in self.xbrls[0].errors:
                raise NoLoadableCSRDFile(
                    f"Could not load the file at {self.report_url} as a CSRD report"
                )
            session.close()

    @property
    def local_datapoint_codes(self) -> list[str]:
        qualified_names = self.esrs_datapoints.keys()

        return [qname.replace("esrs:", "") for qname in qualified_names]

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
                    f"Could not find datapoint with code {datapoint_code}, for report {self.report_url}",
                    datapoint_short_code=datapoint_code,
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
            )

        return datapoints

    def get_esrs_datapoint_values(
        self, datapoint_codes: typing.List[str]
    ) -> list[DataPoint | NoMatchingDatapointsError]:
        """
        Accept a list of datapoint codes, and return the values for those datapoints as dict
        containing list of DataPoint objects, keyed by the datapoint code, or a list containing
        the error if the datapoint is not found.
        """
        document_results: list[DataPoint | NoMatchingDatapointsError] = []
        for datapoint_code in datapoint_codes:
            try:
                datapoints = self._get_datapoints_for_datapoint_code(datapoint_code)
                document_results.extend(datapoints)
            except NoMatchingDatapointsError as ex:
                document_results.extend([ex])

        return document_results
