from typing import Annotated, Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    CoreModeRef,
    CoreRef,
    DefsRef,
    GenerateJsonSchema,
    JsonSchemaMode,
)
from pydantic_extra_types.domain import DomainStr
from tomlkit import (
    TOMLDocument,
    array,
    comment,
    document,
    dump,
    dumps,
    inline_table,
    nl,
    table,
)
from tomlkit.items import (
    AbstractTable as TOMLTable,
)
from tomlkit.items import (
    InlineTable as TOMLInlineTable,
)
from tomlkit.items import (
    Item as TOMLItem,
)

# Modified semver regex, taken from
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string,
# adapted to make the patch version optional, so it will accept eg 0.2, 0.3.
VERSION_NUMBER_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)(?:\.(?P<patch>0|[1-9]\d*))?(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


def validate_http_url(value: str) -> str:
    """
    An annotation for string fields which validates that they are HTTP(s) URLs.
    We can't use HttpUrl directly as the field type as that changes the type of the value.
    Returning `value` here ensures that the field remains a string, even though it's validated
    as an HTTP URL.
    """
    HttpUrl(value)
    return value


HttpUrlStr: TypeAlias = Annotated[str, AfterValidator(validate_http_url)]


class CarbonTxtJsonSchemaGenerator(GenerateJsonSchema):
    """
    Pydantic bakes a parametrized generic's full type argument into its
    $defs key -- e.g. our version-specific `Disclosure[Literal[...]]` ends
    up as `Disclosure_Literal__web-page____other___`. We only parametrize
    Disclosure/Organisation to vary the version-specific doc_type Literal,
    and only ever generate a schema for one version at a time, so we drop
    the generated generic cruft. Note that this assumes that we never include
    two different versions of the disclosure in a single schema version, but I
    think that that's a safe assumption!
    """

    def get_defs_ref(self, core_mode_ref: CoreModeRef) -> DefsRef:
        core_ref, mode = core_mode_ref
        base = core_ref.split("[", 1)[0]
        return super().get_defs_ref((CoreRef(base), mode))


class CarbonTxtModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Override the default schema generation to use our
    # custom generator defined above:
    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = CarbonTxtJsonSchemaGenerator,
        mode: JsonSchemaMode = "validation",
        **kwargs,
    ) -> dict:
        return super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
            **kwargs,
        )

    @property
    def toml_fields(self) -> list[str]:
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
                is_multiline = False
                for item in value:
                    result = toml_for_value(item)
                    if isinstance(result, TOMLInlineTable):
                        # If the contents of the array are inline tables (eg disclosures, services), they are displayed on multiple lines.
                        # If not (eg service_types of a service) they are not.
                        is_multiline = True
                    if result:
                        arr.append(result)
                return arr.multiline(is_multiline)
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

    domain: DomainStr | None
    name: str | None = None
    # TODO: python prefers snake_case.
    # javascript prefers camelCase
    # but kebab-case is arguable more common in URLS
    # how do we support this?
    service_type: list[str] | None | str = None

    def toml_root(self, **_kwargs) -> TOMLDocument | TOMLTable:
        return inline_table()

    @property
    def toml_fields(self) -> list[str]:
        return ["name", "domain", "service_type"]


DisclosureType = TypeVar("DisclosureType")
OtherDisclosureDocType = Literal["other"]

DocTypeT = TypeVar("DocTypeT", bound=str)


class Organisation(CarbonTxtModel, Generic[DisclosureType]):
    """
    An Organisation is the entity making the claim to running its infrastructure
    on green energy. In the very least it should have some disclosures point to, even
    if it is exclusively relying on services from upstream providers for its green claims.
    """

    # The auto-generated name in the JSON schema for generic classes is
    # extremely verbose, we override it with a more sensible one:
    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        return "Organisation"

    disclosures: list[DisclosureType] = Field(..., min_length=1)

    @property
    def toml_fields(self) -> list[str]:
        return ["disclosures"]


class Upstream(CarbonTxtModel):
    """
    Upstream refers to one or more hosted services that the Organisation
    is relying on to operate a digital service, like running a website, or application.
    """

    # organisations that don't use third party providers could plausibly have an
    # empty upstream list. We also either accept providers as a single string representing
    # a domain, or a dictionary containing the fields defined in the Provider model
    services: list[Service | str] | None = None

    @property
    def toml_fields(self) -> list[str]:
        return ["services"]


class Disclosure(CarbonTxtModel, Generic[DocTypeT]):
    """
    Disclosures are essentially supporting documentation shared by an organisation than can
    be to be used to substantiate a claim like running on green energy, and so on.
    """

    # The auto-generated name in the JSON schema for generic classes is
    # extremely verbose, we override it with a more sensible one:
    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        return "Disclosure"

    doc_type: DocTypeT
    url: HttpUrlStr
    domain: DomainStr | None = None

    def toml_root(self, **_kwargs) -> TOMLDocument | TOMLTable:
        return inline_table()

    @property
    def toml_fields(self) -> list[str]:
        return ["doc_type", "url", "domain"]
