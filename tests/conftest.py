import pytest
import pathlib

import structlog

logger = structlog.get_logger()

pytest_plugins = ["http_mocks"]


@pytest.fixture
def minimal_carbon_txt_org():
    """
    A sample minimal carbon.txt file, assuming no upstream, just self hosting with
    all required on their sustainability page
    """
    return """
        [upstream]
        services = []
        [org]
        disclosures = [
            { domain='used-in-tests.carbontxt.org', doc_type = 'sustainability-page', url = 'https://used-in-tests.carbontxt.org/our-climate-record'}
        ]
    """  # noqa


@pytest.fixture
def shorter_carbon_txt_string():
    """
    A shorter carbon.txt file, with credentials for the org, and the short domain-only
    form of upstream providers
    """

    short_string = """
        [upstream]
        services = [
            {domain='sys-ten.com', service_type=['cloud']},
            {domain='cdn.com', service_type=['cdn']},
        ]
        [org]
        disclosures = [
            { domain='www.hillbob.de', doc_type = 'sustainability-page', url = 'https://www.hillbob.de/klimaneutral'}
        ]
    """  # noqa
    return short_string


@pytest.fixture
def multi_domain_carbon_txt_string():
    """
    A longer carbon.txt file where the org has multiple domains, and wants to serve the appropriate
    data for each domain.
    TODO: this might be better to not support this format
    """
    pth = pathlib.Path(__file__)

    carbon_txt_path = pth.parent / "fixtures" / "carbon-txt-test.toml"

    carbon_txt_string = None
    with open(carbon_txt_path) as carb_file:
        carbon_txt_string = carb_file.read()

    return carbon_txt_string


def minimal_carbon_txt_org_with_csrd_file():
    """
    A sample minimal carbon.txt file, assuming no upstream, and
    linking to a CSRD report containing renewables data
    """
    return """
        [upstream]
        services = []
        [org]
        disclosures = [
            { domain='used-in-tests.carbontxt.org', doc_type = 'csrd-report', url = 'https://used-in-tests.carbontxt.org/esrs-e1-efrag-2026-12-31-en.xhtml'}
        ]
    """  # noqa


@pytest.fixture
def valid_html_not_found_page():
    return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 Not Found</title>
        </head>
        <body>
            <h1>404 Not Found</h1>
            <p>The requested URL was not found on this server.</p>
        </body>
        </html>
    """


@pytest.fixture()
def reset_plugin_registry():
    """
    Reset the plugin registry to the default state. We need to do this
    because the plugin framework we have doesn't reset on each test, and
    if we set up a plugin in one test, it can still be active in the next.
    """
    from carbon_txt.plugins import pm  # noqa

    modules = pm.get_plugins()
    logger.debug(f"\n current modules: {modules}")
    for mod in modules:
        logger.debug(f"\n Unregistering plugin {mod}")
        pm.unregister(mod)

    logger.debug(f"\n updated: {pm.get_plugins()}")

    return pm


@pytest.fixture()
def settings_with_active_csrd_greenweb_plugin(reset_plugin_registry, settings):
    settings.ACTIVE_CARBON_TXT_PLUGINS = ["carbon_txt.process_csrd_document"]


@pytest.fixture()
def settings_with_plugin_dir_set(reset_plugin_registry, settings):
    settings.CARBON_TXT_PLUGINS_DIR = "tests/test_plugins"
