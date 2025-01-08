import importlib
import types
import typing

import pluggy

from . import hookspecs

# we import the hookimpl decorator here so that it is easily available to plugins
from .hookspecs import hookimpl  # noqa

pm = pluggy.PluginManager("carbon_txt")

# uncomment these to see the hooks being called
# For more, see the Pluggy docs:
# https://pluggy.readthedocs.io/en/stable/#built-in-tracing
# pm.trace.root.setwriter(print)
# undo = pm.enable_tracing()

pm.add_hookspecs(hookspecs)
pm.load_setuptools_entrypoints("carbon_txt")

# TODO: add default plugins here when we have them (i.e. for parsing CSRD reports, etc)
DEFAULT_PLUGINS: typing.List[str] = []

for plugin in DEFAULT_PLUGINS:
    mod = importlib.import_module(plugin)
    pm.register(mod, plugin)


def module_from_path(path: str, name: str):
    """
    Load a python file at the path `path`, and return it as a module
    with the name `name`.

    """
    # Adapted from  Datatsette's implementation of the code in the blog post below
    # https://github.com/simonw/datasette/blob/main/datasette/utils/__init__.py#L749
    # Adapted from http://sayspy.blogspot.com/2011/07/how-to-import-module-from-just-file.html
    mod = types.ModuleType(name)
    mod.__file__ = path
    with open(path, "r") as file:
        code = compile(file.read(), path, "exec", dont_inherit=True)
    exec(code, mod.__dict__)
    return mod
