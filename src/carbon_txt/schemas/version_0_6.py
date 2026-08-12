from typing import Literal, Self, TypeAlias

from pydantic import model_validator
from pydantic_core import PydanticCustomError

from .common import (
    CarbonTxtModel,
    HttpUrlStr,
    OtherDisclosureDocType,
)
from .common import (
    Organisation as OrganisationV5,
)
from .version_0_5 import (
    CarbonTxtFile as CarbonTxtFileV5,
)
from .version_0_5 import (
    Disclosure as DisclosureV5,
)
from .version_0_5 import (
    SpecificDisclosureDocType as SpecificDisclosureDocTypeV5,
)

SpecificDisclosureDocType: TypeAlias = Literal[
    SpecificDisclosureDocTypeV5, "measurement-data"
]

DisclosureDocType: TypeAlias = Literal[
    SpecificDisclosureDocType, OtherDisclosureDocType
]


class Disclosure(DisclosureV5):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    In the carbontxt version 0.6 syntax, disclosures have all the same fields as in
    version 0.5, plus an optional description string, and we add the new `measurement-data`
    document type to the enumeration of possible values, and the optional ability to refer
    to a list of `certification_schemes` supported by this disclosure.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    doc_type: DisclosureDocType

    description: str | None = None

    certification_schemes: list[str] | None = None


class CertificationScheme(CarbonTxtModel):
    """
    A `CertificationScheme` represents an externally verified commitment by an organization to some level of carbon redution,
    backed by some evidence as disclosures. At a minimum it should refer to a `url` detailing the certification requirements
    and the verifying organization, and an arbitary `id` for reference in `Disclosure` objects. It may optionally include
    a string `title` and `description`.

    """

    id: str
    url: HttpUrlStr
    title: str | None = None
    description: str | None = None


class Organisation(OrganisationV5[Disclosure]):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some disclosures point to, even
    if it is exclusively relying on services from upstream providers for its green claims.
    This class represents the Organization object in version 0.6 which adds support for certification
    scheme declarations.
    """

    certification_schemes: list[CertificationScheme] | None = None

    @model_validator(mode="after")
    def validate_uniqueness_of_certification_scheme_ids(self) -> Self:
        """Check that each defined certification scheme has a unique id"""
        seen = set()
        if self.certification_schemes:
            for cs in self.certification_schemes:
                if cs.id in seen:
                    raise PydanticCustomError(
                        "custom_value_error",
                        "Certification Scheme id  {cs_id} is used more than once in the same carbon.txt document. Certification scheme ids must be unique!",
                        {"cs_id": cs.id},
                    )
                seen.add(cs.id)
        return self

    @model_validator(mode="after")
    def validate_disclosure_certification_scheme_ids(self) -> Self:
        """
        Check that each certification scheme id referenced in the disclosures
        corresponds to a certification scheme which is present in the carbon.txt file.
        """
        ids = {cs.id for cs in (self.certification_schemes or [])}
        for disclosure in self.disclosures:
            for cs_id in disclosure.certification_schemes or []:
                if cs_id not in ids:
                    raise PydanticCustomError(
                        "custom_value_error",
                        "Certification Scheme id {cs_id} does not correspond to a certification_scheme defined in this carbon.txt document. Possible values: {ids}",
                        {"cs_id": cs_id, "ids": ", ".join(ids)},
                    )
        return self


class CarbonTxtFile(CarbonTxtFileV5):
    """
    A carbon.txt file is the data structure that acts as an index for supporting evidence
    for green claims made by a specific organisation. It is intended to links to
    machine readable data or supporting documentation in the public domain.
    This class represents the version 0.6 syntax, which adds an optional description
    attribute for disclosures, the `measurement-data` disclosure type, and support for
    optional certification schemes.
    """

    org: Organisation
