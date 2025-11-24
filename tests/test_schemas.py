import pytest
from pydantic import ValidationError

from carbon_txt.schemas.common import Organisation
from carbon_txt.schemas.version_0_2 import Disclosure


class TestOrganisation:
    def test_organisation_required_disclosures(self):
        """ """
        with pytest.raises(ValidationError):
            Organisation[Disclosure](disclosures=[])
