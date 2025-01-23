

# ADR 1: Adding functionality via a plugin system for the carbon.txt validator

## Status

Accepted

## Context

Part of our work on the carbon.txt project is to build a carbon.txt validator - an open source piece of software designed to validate carbon.txt files based on their contents.

We want to grow an ecosystem based around the idea of using publicly disclosed, machine readable information that is coming into the public domain as a result of new laws. We want the investment we have made into building tooling to fetch and validate carbon.txt files to be something that be useful for other groups wanting to work with this data too.


## Decision

**What is the change that we're proposing and/or doing?**

We would introduce a plugin system to the carbon.txt validator to allow new plugins adjust and extend the functionlity without needing to change the core code.

These would "hook into" various stages of the lifecycle validating a carbon.txt file.

### What kind of functionality we expect to support.

A plugin system like this would allow us to support actions like:

- **looking for new kinds of evidence we look for when an organisation is trying to back claims** - like CSRD reports, EED submissions or similar.
- **changing the information the validator looks for within the evidence linked from a carbon.txt file** - we look for informatino about green energy, but some evidence forms have rich data related to other domains.
- **archiving the evidence linked in a carbon.txt file.to cheap, redundant storage for later reference** in case they change


## How it would work

### What plugin system is being proposed?

The proposed approach is to use widely used plugin framework in the python ecosystem called [Pluggy](https://pluggy.readthedocs.io/).

A number of well known python projects use this plugin, like [Datasette](https://docs.datasette.io/en/stable/writing_plugins.html#writing-one-off-plugins), [LLM](https://llm.datasette.io/en/stable/plugins/index.html), [Pytest](https://docs.pytest.org/en/latest/how-to/writing_plugins.html#pip-installable-plugins), [Tox](https://tox.wiki/en/latest/plugins.html#) and others. It is well documented and battle tested.

#### How does Pluggy work?

Pluggy allows a **host program**, (in our case the carbon.txt validator), to be extended by defining specific **hooks** in the lifecycle of a program or serving a request.

This allows code in plugins to intervene at these specific points in the lifecycle, by implementing these **hook functions** themselves.

At runtime, code in these plugins is added to a **Plugin Registry**, and the functions that match a given **hook** are then called by the **host program**, passing in arguments to the plugin function code as specified in the original hook.

#### A concrete use case

For example, we have a predefined set of documents we accept in our current spec for carbon.txt, which is listed in a schema. We might define a hook with the name `process_document`, that accepts a `document` as an argument to be passed into it.

In a plugin, we would then implement the `process_document` hook function, which includes specific logic for working with that document in a desired way. In our case we might use this hook to fetch a file at the URL specified by the document, or parse the linked document look for specific information about green energy in the document.

We have a CSRD processor class in the project codebase that is designed to parse CSRD documents, and we would query the document in this `process_document` function, returning the results of querying for specific information.

### What initial hooks would we consider?

We have a few candidate hooks to start with.

#### Register document type

This, when run on startup extends our schema, to support new document types we might look for in a carbon.txt file.

A concrete example might be a `CSRD-Report` document type if we don't support it already, or an `EED Submission` document type to represent the structured data that companies need to disclose as a result of the Energy Efficiency Directive. [See more on the Green Web Foundation blog](https://www.thegreenwebfoundation.org/news/happy-e-e-d-day-to-those-who-celebrate/)

When parsing a document, we would reflect this new document type in the Validation Schema used, so that a `EED Submission` would be considered a valid document type in validation life cycle.

A mechanism like this would allow for new kinds of evidence to be supported and anyone to prototype support for new kinds of documents in the carbon.txt spec.

#### Process document

This hook, when run after the initial validation of the carbon.txt file syntax would support further processing of documents lined in the carbon.txt file. This might take the form of further validation steps, or other steps to process as outlined above in _What functionality to we expect to support_

The hook function would run for each document linked in a carbon.txt file, accepting a reference to the document, and would return a list of new data structures created as a result of processing the document..

A concrete example would be processing a CSRD Report document linked in a report, and returning a datastructure containing the specific datapoints fetched from the report.

Another example would be processing each linked webpage, to download a copy of the page and save a timestamped version to object storage. In this case the returned values might be a datastructure containing the links to the stored files, once they have been saved to object storage.

### How will functionality in plugins be loaded into the main validator?

We add support for plugins by adding a **Plugin Manager** to our Validator, that is responsible for tracking plugins, as well as calling the code in them.

The Plugin Manager in Pluggy supports a number of ways to add plugins to an internal **Plugin Registry**, registering the code to be run at predefined stages of the life cycle of an application.

Projects using it tend to support the registering of plugins three main ways:

1. registering 'internal' plugins defined in the project code base
2. registering 'external' plugins in a pre-defined directory that is detected at run-time.
3. registering 'external' pre-built plugins added to the active environment a project

#### 1. Registering internal plugins:

There will often be functionality in a project that could have been implemented using the same plugin hooks as offered to external projects. In many cases internal plugins use these same hooks, and are loaded in by default on startup, to provide a some default functionality.

On startup, code like the sample project code below loads the plugins to add the functionality in the plugins to the host program:

```python
DEFAULT_PLUGINS = ('myproject.internal_plugin1', 'myproject.internal_plugin2')

# Load default plugins
for plugin in DEFAULT_PLUGINS:
    # load the plugin into memory as a python module, `mod`
    mod = importlib.import_module(plugin)

    # assume 'pm' is the object responsible for controlling access to the Plugin Registry
    pm.register(mod, plugin)
```

These provide a convenient package of default functionality that can be changed by overrriding the DEFAULT_PLUGINS variable to use different plugins.

These also work as evidence of 'dogfooding' (using the same plugin APIs and interfaces we expect others to use).


#### 2. Registering external plugins:

An idiomatic way to allow third party code to be used as a plugin by Pluggy is to define a plugin directory to place code into, and load it at run-time.

The Datasette project does this. This allows people to download the published package containing the Datasette command line tool, and then register a single file plugin placed in a directory specified by a command line flag when running the command line tool.

**Using this approach with our Validator**

If we had this plugin system in our `carbon-txt` validator, implementation would look as follows.

1.wWe would create a python file called `example-plugin.py` like so:

```python
# ./plugins-directory/example-plugin.py
from carbon_txt import hookimpl

@hookimpl
def process_document(document):
    # assume do_some_work is a function defined elsewhere
    if document.doc_type == "csrd-report":
        results = do_some_work(document)
        return results

```

This plugin would be saved in the directory `plugins-directory`. We would then include the plugin's functionality by specifying the directory `--plugin-dir ./plugins-directory/` when we run the validator on the command line:

```
carbon-txt serve --plugin-dir ./plugins-directory/`
```

Internally code at startup searches for valid files in the specified `plugins-directory` directory. the code below is slightly edited implementation from [the Datasette project](https://github.com/simonw/datasette/blob/main/datasette/app.py#L399-L408), and in ours would be similar:

```python
# assume our CLI lets us specify a plugins directory to look for plugins in, specified by plugins_dir

if self.plugins_dir:

    for filepath in glob.glob(os.path.join(self.plugins_dir, "*.py")):
        if not os.path.isfile(filepath):
            continue

        # load chosen python file importing the code as a module
        mod = module_from_path(filepath, name=os.path.basename(filepath))

        try:
            # add the module to the Plugin Registry, `pm`
            pm.register(mod)
        except ValueError:
            # Plugin already registered
            pass
```

The benefit of this approach is that it supports extending a project using our `carbon-txt` validator with simple one-off plugins to add required functionality, and it does this without the author needing to change the original core validator project code.

Datasette's own [documentation shows how to use this approach to write simple plugins](https://docs.datasette.io/en/stable/writing_plugins.html#writing-one-off-plugins). This would likely the first tutorial we offer for people looking to create their own plugins themselves, and would support teams looking to create internal plugins on existing projects.

This would not work so well for making external plugins re-usable by others, to help create an ecosystem.

For that, a third approach is common for making plugins available for others to use. For this approach an author must build and publish a python package containing the plugin to an external repository for others to download and use.


#### 3. Registering 'external' pre-built plugins

The final common approach is to offer support for plugins that have already been built and published to repository, like Pypu, or Github. When these plugins are installed into a project using common installation commands like `pip install`, they contain the code that will be run to make the plugin visible to the Pluggy plugin manager and added to its plugin registry.

For this to be possible, plugins need to be packaged for distribution, and contain a `pyproject.toml` file containing metadata about the project that lays out which files should be made accessible to the appropriate **host** project using Pluggy - in our case the carbon-txt Validator.

In the sample below our **host project** with the plugin system is identified with the `[project.entry-points.carbon_txt]` toml snippet, and the relevant code in the project is identified by the snippet `myproject = "myproject.pluginmodule"`

```toml
# sample ./pyproject.toml file

# hatchling is a default build system in python when creating python packages
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myproject"

[project.entry-points.carbon_txt]
myproject = "myproject.pluginmodule"
```

On startup of the validator, would initialise the Pluggy plugin manager, which discovers code in external plugins by looking up for a specific "entry point" as outlined above in every installed project. Nothing else needs to be done - these plugins would be included by default by the plugin manager in our host validator programme every time thhe project is run.


#### Further control over which plugins to use when running code

Most projects that use Pluggy provide further support for finer-grained control of which plugins to keep active.

Command line flags like `disabled_plugins=plugin1,plugin2` are common, as are having specific named settings in the host program. We already support external config files in our `carbon-txt` command line tool. This allows us to set values for `DEFAULT_PLUGINS` in a sensible place that are easy to override.


## Consequences

**What becomes easier or more difficult to do because of this change?**

Extending the functionality without access to the main codebase becomes easier with this system, as long as the exposed "hooks" are well thought through, and useful.

The system can become harder to change, if people grow reliant on a given "hook" working a specific way.

If we learn that our initial approach for implementing a feature needs rethinking, or parts of our design need the same, then we need a way to communicate changes to anyone 'downstream'.

For this reason, it's better to be conservative with introducing hooks, and only doing so when we are confident they have a concrete use case that is valuable. When adding hooks, we should also add at least one demonstration plugin using the hook.
