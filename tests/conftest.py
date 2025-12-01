import pytest

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


@pytest.fixture()
def version_0_2_carbon_txt_full():
    with open("tests/fixtures/version_0.2/full.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_2_carbon_txt_no_disclosure_domain():
    with open("tests/fixtures/version_0.2/no_disclosure_domain.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_2_carbon_txt_no_explicit_version():
    with open("tests/fixtures/version_0.2/no_explicit_version.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_2_carbon_txt_no_upstreams():
    with open("tests/fixtures/version_0.2/no_upstreams.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_3_carbon_txt_full():
    with open("tests/fixtures/version_0.3/full.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_3_carbon_txt_no_last_updated():
    with open("tests/fixtures/version_0.3/no_last_updated.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_3_carbon_txt_no_disclosure_domain():
    with open("tests/fixtures/version_0.3/no_disclosure_domain.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_3_carbon_txt_no_disclosure_valid_until():
    with open("tests/fixtures/version_0.3/no_disclosure_valid_until.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_3_carbon_txt_no_upstreams():
    with open("tests/fixtures/version_0.3/no_upstreams.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_full():
    with open("tests/fixtures/version_0.4/full.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_no_last_updated():
    with open("tests/fixtures/version_0.4/no_last_updated.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_no_disclosure_domain():
    with open("tests/fixtures/version_0.4/no_disclosure_domain.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_no_disclosure_valid_until():
    with open("tests/fixtures/version_0.4/no_disclosure_valid_until.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_no_disclosure_title():
    with open("tests/fixtures/version_0.4/no_disclosure_title.toml") as file:
        return file.read()


@pytest.fixture()
def version_0_4_carbon_txt_no_upstreams():
    with open("tests/fixtures/version_0.4/no_upstreams.toml") as file:
        return file.read()
