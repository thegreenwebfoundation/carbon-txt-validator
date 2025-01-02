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
def __(form_datapoint_values, mo):
    form = (
        mo.md("""
        **Your form.**

        {url}

        {datapoint}
    """)
        .batch(
            url=mo.ui.text(placeholder="Url to fetch CSRD file from", full_width=True),
            datapoint=mo.ui.dropdown(
                options=form_datapoint_values,
                label="chosen data point",
            ),
        )
        .form(show_clear_button=True, bordered=False)
    )
    form
    return (form,)


@app.cell
def __(NoLoadableCSRDFile, check_csrd_report, form):
    parsed_report_data = None

    if form.value:
        _url = form.value.get("url")
        if _url:
            try:
                parsed_report_data = check_csrd_report(form.value.get("url"))
            except NoLoadableCSRDFile:
                # we can't load the file, fail gracefully and show the error below
                pass
    parsed_report_data
    return (parsed_report_data,)


@app.cell
def __(form, parsed_report_data):
    def fetch_datapoints():
        if parsed_report_data:
            return parsed_report_data.get_esrs_datapoint_values(
                [form.value["datapoint"]]
            )

    vals = fetch_datapoints()
    return fetch_datapoints, vals


@app.cell
def __(processors):
    def show_datapoint_values():
        form_options = {}
        for item in processors.CSRDProcessor.esrs_datapoints.items():
            form_options[item[1]] = item[0].replace("esrs:", "")

        return form_options

    form_datapoint_values = show_datapoint_values()
    return form_datapoint_values, show_datapoint_values


@app.cell
def __(form, mo, vals):
    from carbon_txt.processors import DataPoint, NoMatchingDatapointsError

    message = None

    if form.value and vals:
        first_datapoint, *rest = vals.get(form.value["datapoint"])
        if first_datapoint.unit == "percentage":
            datapoint_value = f"{first_datapoint.value:.2%}"
        else:
            datapoint_value = first_datapoint.value

        if first_datapoint and isinstance(first_datapoint, DataPoint):
            message = f"""

            {first_datapoint.name} was {datapoint_value}
            between {first_datapoint.start_date} and {first_datapoint.end_date}.
            """

    mo.md(message).callout(kind="success") if message else None
    return (
        DataPoint,
        NoMatchingDatapointsError,
        datapoint_value,
        first_datapoint,
        message,
        rest,
    )


@app.cell
def __(NoMatchingDatapointsError, form, mo, vals):
    error_message = None

    if form.value and vals:
        if isinstance(
            vals[form.value["datapoint"]][0],
            NoMatchingDatapointsError,
        ):
            parse_errors = vals[form.value["datapoint"]][0].__str__()
            error_message = f"""
            Sorry, we couldn't find any values for {form.value['datapoint']} datapoint.

            Error was:

            {parse_errors}
            """

    if form.value and form.value["url"] and not vals:
        error_message = f"Sorry, we were unable to load the file at {form.value['url']}. Is it definitely reachable and a valid XML file?"

    mo.md(error_message).callout(kind="danger") if error_message else None
    return error_message, parse_errors


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
