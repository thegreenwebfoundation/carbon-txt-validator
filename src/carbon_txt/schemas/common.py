from typing import Optional, List, Literal, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, Field

from tomlkit import (
    comment,
    document,
    nl,
    table,
    dumps,
    dump,
    inline_table,
    array,
    TOMLDocument,
)

from tomlkit.items import AbstractTable as TOMLTable, Item as TOMLItem

# Modified semver regex, taken from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string,
# adapted to make the patch version optional, so it will accept eg 0.2, 0.3.
VERSION_NUMBER_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)(?:\.(?P<patch>0|[1-9]\d*))?(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


class CarbonTxtModel(BaseModel):
    @property
    def toml_fields(self) -> List[str]:
        """
        To be overridden in subclasses - returns the names
        of the fields to be serialized to TOML, in order.
        """
        return []

    def toml_root(self, **_kwargs) -> TOMLDocument | TOMLTable:
        """
        To be optionally overridden in subclasses -
        returns the tomlkit object to be used to
        construct the serialization
        """
        return table()

    def toml_tree(self, **kwargs) -> TOMLDocument | TOMLTable:
        """
        Assembles the tomlkit object for this object's serialization,
        recursively calling the same method on all properties.
        """

        def toml_for_value(value):
            if isinstance(value, list):
                arr = array()
                for item in value:
                    result = toml_for_value(item)
                    if result:
                        arr.append(result)
                return arr
            elif isinstance(value, CarbonTxtModel):
                result = value.toml_tree(**kwargs)
                if isinstance(result, TOMLItem):
                    return result
            else:
                return value

        doc = self.toml_root(**kwargs)
        for field in self.toml_fields:
            value = getattr(self, field)
            formatted_value = toml_for_value(value)
            if formatted_value is not None:
                doc.add(field, formatted_value)
        return doc

    def to_toml(self, **kwargs) -> str:
        """
        Return a TOML serialization of this object as a string.
        Passes its kwargs to the toml_root and toml_tree methods
        of all objects in the syntax tree.
        """
        return dumps(self.toml_tree(**kwargs))

    def save_toml(self, path, **kwargs) -> None:
        """
        Writes out a TOML serialization of this object to the given filename.
        Passes its kwargs to the toml_root and toml_tree methods
        of all objects in the syntax tree.
        """
        with open(path, "w") as file:
            return dump(self.toml_tree(**kwargs), file)


class CarbonTxtFile(CarbonTxtModel):
    def toml_root(self, **kwargs) -> TOMLDocument:
        """
        The root TOML object takes an optional header_comment kwargs
        which allows us to specify a comment to be placed at the top
        of the generated TOML. This is useful in situations where we
        might generate multiple carbon.txt files for different domains
        and need to keep track of which domain which file refers to.
        """
        doc = document()
        if "header_comment" in kwargs:
            header_comment: str = kwargs["header_comment"]
            doc.add(comment(header_comment))
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

    def toml_root(self, **_kwargs) -> TOMLDocument | TOMLTable:
        return inline_table()

    @property
    def toml_fields(self) -> List[str]:
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
    def toml_fields(self) -> List[str]:
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
    def toml_fields(self) -> List[str]:
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

    def toml_root(self, **_kwargs) -> TOMLDocument | TOMLTable:
        return inline_table()

    @property
    def toml_fields(self) -> List[str]:
        return ["doc_type", "url", "domain"]
