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

    fetch_datapoints()
    return (fetch_datapoints,)


@app.cell
def __(parsed_report_data):
    def show_datapoint_values():
        if parsed_report_data:
            return parsed_report_data.get_esrs_datapoint_values(
                parsed_report_data.esrs_datapoints[0]
            )

    show_datapoint_values()
    return (show_datapoint_values,)


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
