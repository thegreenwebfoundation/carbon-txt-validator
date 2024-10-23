import pytest
import pathlib


@pytest.fixture
def minimal_carbon_txt_org():
    """
    A sample minimal carbon.txt file, assuming no upstream, just self hosting with
    all required on their sustainability page
    """
    return """
        [upstream]
        providers = []
        [org]
        credentials = [
            { domain='used-in-tests.carbontxt.org', doctype = 'sustainability-page', url = 'https://used-in-tests.carbontxt.org/our-climate-record'}
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
        providers = [
        'sys-ten.com',
        'cdn.com',
        ]
        [org]
        credentials = [
            { domain='www.hillbob.de', doctype = 'sustainability-page', url = 'https://www.hillbob.de/klimaneutral'}
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
