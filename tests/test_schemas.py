import pytest
from carbon_txt.schemas import Organisation  # type: ignore

from pydantic import ValidationError


class TestOrganisation:
    def test_organisation_required_disclosures(self):
        """ """
        with pytest.raises(ValidationError):
            Organisation(disclosures=[])
