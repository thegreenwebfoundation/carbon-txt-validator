from pluggy import HookimplMarker
from pluggy import HookspecMarker

hookspec = HookspecMarker("carbon_txt")
hookimpl = HookimplMarker("carbon_txt")


@hookspec
def register_command(app):
    """Fires directly after Carbon.txt validator first starts running"""


@hookspec
def register_document_type(schema):
    """Returns the schema with support for the new document types added"""


@hookspec
def process_document(document, parsed_carbon_txt_file, logs):
    """Processes the supplied supporting evidence document, returning the results of processing it"""
