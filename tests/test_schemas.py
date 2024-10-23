import pytest
from carbon_txt_validator.schemas import Organisation

from pydantic import ValidationError


class TestOrganisation:
    def test_organisation_required_credentials(self):
        """ """
        with pytest.raises(ValidationError):
            org = Organisation(credentials=[])
