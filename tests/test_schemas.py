import pytest
from pydantic import ValidationError

from carbon_txt.schemas.common import Organisation
from carbon_txt.schemas.version_0_6 import Disclosure
from carbon_txt.schemas.version_0_6 import CarbonTxtFile as CarbonTxtFile0_6


class TestOrganisation:
    def test_organisation_required_disclosures(self):
        with pytest.raises(ValidationError):
            Organisation[Disclosure](disclosures=[])


class TestVersion0_6CertificationSchemeUniqueness:
    def test_duplicate_certification_scheme_ids_are_rejected(self):
        """
        ADR-6 states certification scheme ids must be unique within a
        carbon.txt file.
        There is a `validate_uniqueness_of_certification_scheme_ids` validator
        which is an  unimplemented stub, so duplicate ids currently validate
        without error.
        This test is expected to fail until the validator is implemented.
        """
        data = {
            "version": "0.6",
            "org": {
                "certification_schemes": [
                    {"id": "b-corp", "url": "https://example.com/one"},
                    {"id": "b-corp", "url": "https://example.com/two"},
                ],
                "disclosures": [
                    {"doc_type": "web-page", "url": "https://example.com/page"}
                ],
            },
        }

        with pytest.raises(ValidationError):
            CarbonTxtFile0_6.model_validate(data)
