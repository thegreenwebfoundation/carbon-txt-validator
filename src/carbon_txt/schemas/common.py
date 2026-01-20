from typing import Optional, List, Literal, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field

from tomlkit import comment, document, nl, table, dumps, inline_table, array

# Modified semver regex, taken from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string,
# adapted to make the patch version optional, so it will accept eg 0.2, 0.3.
VERSION_NUMBER_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)(?:\.(?P<patch>0|[1-9]\d*))?(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class CarbonTxtModel(BaseModel):
    @property
    def toml_fields(_self):
        return []

    @property
    def toml_root(_self):
        return table()

    def toml_tree(self):
        def toml_for_value(value):
            if isinstance(value, list):
                arr = array()
                arr.extend([toml_for_value(item) for item in value])
                return arr
            elif isinstance(value, CarbonTxtModel):
                return value.toml_tree()
            else:
                return value

        doc = self.toml_root
        for field in self.toml_fields:
            value = getattr(self, field)
            formatted_value = toml_for_value(value)
            if formatted_value is not None:
                doc.add(field, formatted_value)
        return doc

    def to_toml(self):
        return dumps(self.toml_tree())


class CarbonTxtFile(CarbonTxtModel):
    @property
    def toml_root(self):
        doc = document()
        doc.add(
            comment(
                "This is an automatically generated carbon.txt file! For further details see https://carbontxt.org"
            )
        )
        doc.add(nl())
        return doc


class Service(CarbonTxtModel):
    """
    A service in this context is a hosted service, offered by a provider
    of hosted services.
    The domain is used as key for looking up a corresponding provider in the
    Green Web Platform
    """

    model_config = ConfigDict(extra="forbid")

    domain: Optional[str]
    name: Optional[str] = None
    # TODO: python prefers snake_case.
    # javascript prefers camelCase
    # but kebab-case is arguable more common in URLS
    # how do we support this?
    service_type: Optional[List[str]] | str = None

    @property
    def toml_root(_self):
        return inline_table()

    @property
    def toml_fields(_self):
        return ["name", "domain", "service_type"]


DisclosureType = TypeVar("DisclosureType")


class Organisation(CarbonTxtModel, Generic[DisclosureType]):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some disclosures point to, even
    if it is exclusively relying on services from upstream providers for its green claims.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Organisation"

    model_config = ConfigDict(extra="forbid")
    disclosures: List[DisclosureType] = Field(..., min_length=1)

    @property
    def toml_fields(_self):
        return ["disclosures"]


class Upstream(CarbonTxtModel):
    """
    Upstream refers to one or more hosted services that the Organisation
    is relying on to operate a digital service, like running a website, or application.
    """

    model_config = ConfigDict(extra="forbid")

    # organisations that don't use third party providers could plausibly have an
    # empty upstream list. We also either accept providers as a single string representing
    # a domain, or a dictionary containing the fields defined in the Provider model
    services: Optional[List[Service | str]] = None

    @property
    def toml_fields(_self):
        return ["services"]


class Disclosure(CarbonTxtModel):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    """

    # __name__ must be overridden so that Pydantic uses the correct type
    # name in the generated JSON schema
    __name__ = "Disclosure"

    model_config = ConfigDict(extra="forbid")
    doc_type: Literal[
        "web-page",
        "annual-report",
        "sustainability-page",
        "certificate",
        "csrd-report",
        "other",
    ]
    url: str
    domain: Optional[str] = None

    @property
    def toml_root(_self):
        return inline_table()

    @property
    def toml_fields(_self):
        return ["doc_type", "url", "domain"]
