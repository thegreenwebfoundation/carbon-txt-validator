import marimo

__generated_with = "0.9.23"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        r"""
        # Experimenting with how to query pythonically with Arelle

        I want to be able to pull out a specific value from an CSRD report for a reporting organisation I am interested in.

        I want to make it trivial for others _to do as well_, assuming the CSRD report is online.

        So let's build a way to check for a given value for any CSRD file that is online.

        The law in Europe **literally says it should be online on a company website in 2025**, so it seems like a reasonable thing to ask for, right?
        """
    )
    return


@app.cell
def __(mo):
    mo.md("""### First add some helpful libraries""")
    return


@app.cell
def __():
    import marimo as mo

    return (mo,)


@app.cell
def __():
    import pathlib

    from arelle.api.Session import Session
    from arelle.logging.handlers.StructuredMessageLogHandler import (
        StructuredMessageLogHandler,
    )
    from arelle.RuntimeOptions import RuntimeOptions

    return RuntimeOptions, Session, StructuredMessageLogHandler, pathlib


@app.cell
def __(mo):
    mo.md(
        r"""
        ### Next, let's figure out how to start a session using Arelle's Python API

        We want to try opening a session, passing in the relevant RuntimeOptions, which happen to include the path to our CSRD report.

        We'll then see if we can get an XBRL model, to manipulate once it's a handy datastructure.
        """
    )
    return


@app.cell
def __(RuntimeOptions, Session, pathlib):
    # this file is the same one as in this gist
    # https://gist.github.com/mrchrisadams/fb14e79d2d52977255c0b1db6de86726
    path_to_remote_file = "https://gist.githubusercontent.com/mrchrisadams/fb14e79d2d52977255c0b1db6de86726/raw/5536eb17470125912a62684789df35a440dbed4a/efrag-2026-12-31-en.xhtml"

    path_to_local_file = "data/Set1/InlineXBRL/ESRS-E1/efrag-2026-12-31-en.xbrl"
    sample_csrd_file = pathlib.Path(path_to_local_file).exists()

    # this
    options = RuntimeOptions(
        entrypointFile=str(path_to_remote_file),
        internetConnectivity="online",
        keepOpen=True,
        logFormat="[%(messageCode)s] %(message)s - %(file)s",
        logPropagate=False,
    )

    with Session() as session:
        sesh = session.run(options)
        model_xbrls = session.get_models()

    # marimo is conceptually similar to iPython notebook, but
    model_xbrls
    return (
        model_xbrls,
        options,
        path_to_local_file,
        path_to_remote_file,
        sample_csrd_file,
        sesh,
        session,
    )


@app.cell
def __(mo):
    mo.md(
        r"""
        ### OK, now have more model. What's in it? how do we access anything?

        By default, model_xbrls is a list of individual `xbrl_model` options.

        Inside this model are a bunch of **facts** all of which correspond to a concept listed in the European Sustainability Reporting Standards.

        We are a tiny NGO, that cares about a fossil free internet, and we think the data being disclosed by affected companies is important for a richer public discourse around decarbonising our economy. The link below jumps right to the key part of a big report we wrote about making used of new sustainability laws to make sustainablity data more discoverable and accessible. It has some helpful digrams, and should help explain why the green web foundation is doing some of this work:

        https://www.thegreenwebfoundation.org/publications/carbon-txt-energy-efficiency-briefing/#ib-toc-anchor-41

        Anyway, let's the see the model
        """
    )
    return


@app.cell
def __(model_xbrls):
    model_xbrl = model_xbrls[0]
    model_xbrl.factsByQname
    return (model_xbrl,)


@app.cell
def __(mo):
    mo.md(
        """
        ### Is the first specific datapoint we care about in there?

        Yup, it looks like it is. woot!
        """
    )
    return


@app.cell
def __(model_xbrl):
    chosen_data_point = "esrs:PercentageOfRenewableSourcesInTotalEnergyConsumption"
    [
        key
        for key in model_xbrl.factsByQname.keys()
        # only return the one we want to see as a test run
        if str(key) == chosen_data_point
    ]
    return (chosen_data_point,)


@app.cell
def __(mo):
    mo.md(
        r"""
        ### Accessing the actual value.

        For reasons I don't quite understand, I can't access a fact by doing `model_xbrl.factsByQname.get(chosen_data_point)`.

        So, the code below uses a list comprehension which is likely slow, but it does work.
        """
    )
    return


@app.cell
def __(chosen_data_point, model_xbrl):
    matching_facts = [
        fact
        for fact in model_xbrl.facts
        if chosen_data_point in str(fact.concept.qname)
    ]

    org_renewables = matching_facts[0]
    return matching_facts, org_renewables


@app.cell
def __(mo):
    mo.md(
        r"""
        ### Ah ha! We have it!

        OK, we have what looks like the matching fact. We're expecting the figure to be something like 23%.

        Let's see if it is that. We can turn it into a `dict` to see a bunch of other values.
        """
    )
    return


@app.cell
def __(org_renewables):
    org_renewables
    return


@app.cell
def __(org_renewables):
    org_renewables.__dict__
    return


@app.cell
def __(mo, org_renewables):
    mo.md(f"""
    ### Our figure for percentage of renewables sources in total energy consumption is {float(org_renewables.value):.2%}

    Read more at: https://xbrl.efrag.org/e-esrs/esrs-set1-2023.html#4886
    """)
    return


@app.cell
def __(org_renewables, path_to_remote_file):
    print(
        f"Our value for the report at {path_to_remote_file} is {float(org_renewables.value):.2%}"
    )
    return


@app.cell
def __(model_xbrls):
    model_xbrls
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
