import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def __(mo):
    mo.md("""# Checking CSRD files remotely""")
    return


@app.cell
def __():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def __(mo):
    mo.md("""## Let's check a CSRD report to see if it has the stuff we expected!""")
    return


@app.cell
def __():
    from carbon_txt import processors

    return (processors,)


@app.cell
def __(processors):
    def check_csrd_report(url):
        processor = processors.CSRDProcessor(url)

        return processor

    return (check_csrd_report,)


@app.cell
def __(mo):
    form = (
        mo.md("""
        **Your form.**

        {url}

        {datapoint}
    """)
        .batch(
            url=mo.ui.text(placeholder="Url to fetch CSRD file from", full_width=True),
            datapoint=mo.ui.dropdown(
                options=["PercentageOfRenewableSourcesInTotalEnergyConsumption"],
                label="chosen data point",
            ),
        )
        .form(show_clear_button=True, bordered=False)
    )
    form
    return (form,)


@app.cell
def __(check_csrd_report, form):
    parsed_report_data = None

    if form.value:
        _url = form.value.get("url")
        if _url:
            parsed_report_data = check_csrd_report(form.value.get("url"))
    parsed_report_data
    return (parsed_report_data,)


@app.cell
def __(parsed_report_data):
    def fetch_datapoints():
        if parsed_report_data:
            return parsed_report_data.esrs_datapoints[0]

    vals = fetch_datapoints()
    return fetch_datapoints, vals


@app.cell
def __(parsed_report_data):
    def show_datapoint_values():
        if parsed_report_data:
            vals = parsed_report_data.get_esrs_datapoint_values(
                [parsed_report_data.esrs_datapoints[0]]
            )
            return vals

    val = show_datapoint_values()
    val
    return show_datapoint_values, val


@app.cell
def __(mo, val):
    from carbon_txt.processors import DataPoint, NoMatchingDatapointsError

    message = None

    if isinstance(
        val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0], DataPoint
    ):
        message = f"""
        {val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0].name} was  {val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0].value:.2%} between {val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0].start_date} and {val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0].end_date}.
        """

    mo.md(message).callout(kind="success") if message else None
    return DataPoint, NoMatchingDatapointsError, message


@app.cell
def __(NoMatchingDatapointsError, mo, val):
    error_message = None
    if isinstance(
        val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][0],
        NoMatchingDatapointsError,
    ):
        parse_errors = val["PercentageOfRenewableSourcesInTotalEnergyConsumption"][
            0
        ].__str__()
        error_message = f"""
        Sorry, we couldn't find any values for 'Percentage Of Renewable Sources In Total Energy Consumption' datapoint.

        Error was:

        {parse_errors}
        """

    mo.md(error_message).callout(kind="danger") if error_message else None
    return error_message, parse_errors


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
