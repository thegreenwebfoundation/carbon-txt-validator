# Extending the Carbon.txt Validator with plugins


```{admonition} Warning
:class: warning
This content is in flux, and subject to change. It may be moved to our [developer site](https://developers.thegreenwebfoundation.org/)
```

## How to implement plugins for the carbon.txt validator

The carbon-txt validator is designed to support extending its functionality via a plugin system, and there are two supported ways to do use it.

1. **Internal plugins for internal use**, via the `--plugins-dir` command line flag
2. **Publishing plugins for others to use**, as a Python Package

Under the hood, the system uses [Pluggy](https://pluggy.readthedocs.io/), a widely used framework for building plugin systems, based around exposing a set of "hooks", at various stages of the lifecycle of running the validator.

By implmenting functions that use the appropriate hook, you can extend the functionlaity of the carbon.txt validator.

A number of well known python projects use this plugin, like [Datasette](https://docs.datasette.io/en/stable/writing_plugins.html#writing-one-off-plugins), [LLM](https://llm.datasette.io/en/stable/plugins/index.html), [Pytest](https://docs.pytest.org/en/latest/how-to/writing_plugins.html#pip-installable-plugins), [Tox](https://tox.wiki/en/latest/plugins.html#) and others. It is well documented and battle tested.

## Making one-off projects for internal use

As an example, carbon.txt files are intended to make the underlying data and supporting evidence for green claims easy to find. So, when a carbon.file links to this data, one thing you might want to do is see if the linked files are publicly accessible online.

One way to do this would be to build a plugin specifically to check that files linked in a carbon.txt file are accessible, by sending a HEAD request over HTTP, to see if ths file is still reachable.

To do this, we need to choose the right "hook" to implement, and we need to decide how we'll make that HTTP request to it.

We know that every `Organisation` using a carbon.txt file making green claims needs to back them up with supporting evidence in the form of `Credentials`, and each `Credential` contains a hyperlink to a file online, at a given `url`.

So, every time we see an `url`, we need to send an HTTP request to see if the file is still reachable. The carbon.txt validator bundles the [httpx](https://www.python-httpx.org/) HTTP client library, so we can use that to send the appropriate request.


### Create a new python file implementing the appropriate hook.

Checking the plugin hook list online, we see a `process_document` hook we can uses, that fires for every single `Credential` document linked in a carbon.txt file. So, we use that `hook` to implement.

In a new python file we would implement a method _with the same name as our desired hook_, and with the `@hookimpl` decorator applied to the method. This is how our plugin system knows to run it.


```python
# saved to ./my_plugins/check_file_online.py

import logging

import httpx
from carbon_txt.plugins import hookimpl

# every plugin needs a name
plugin_name = "carbon_txt_check_online"


@hookimpl
def process_document(document, logs):
    # we send a HEAD request, as we are not trying to download the file.
    # and check the contents - we just want to see that it's reachable
    response = httpx.head(document.url, follow_redirects=True)

    if response.status_code == 200:
        logs.append(f"{plugin_name}: File is online: {document.url}")
        file_online = True
    else:
        logs.append(f"{plugin_name}: File is offline: {document.url}")
        file_online = False

    check_results = {
        "url": document.url,
        "file_online": file_online,
    }

    # because processing a document can result in multiple results being
    # returned we always return a list of results
    results = [check_results]

    return {
        # return the logs so we see the output in response seen by the user
        "logs": logs,
        # return the name of the plugin, so we can tell the output plugins apart
        "plugin_name": plugin_name,
        # return the results of prcoessing the document - in our case a
        # check to see if it's online
        "document_results": results,
    }


```

### Make sure the file is accessible when calling the carbon-txt command line tool

Now we have a file, we need a way for the carbon.txt validator to find it and run it.

Create a directory, `my_plugins`, in the same directory in a project directory where you expect to run the `carbon-txt` binary .

We then move the file to `my_plugins/check_file_online.py`.

### Run the `carbon-txt` command line tool with the `--plugin-dirs` flag

Finally we run the `carbon-txt` command line tool, with the `--plugin-dirs` flag, and the path to `my_plugins` the directory containing our new plugin.

If we want to check a given domain's carbon.txt file, AND check the linked files ae online, we run our usual command, with the extra flags:

```
carbon-txt validate domain used-in-tests.carbontxt.org --plugins-dir my_plugins/
```

Our output should look something like the output below, with the extra `Results of processing linked documents in the carbon.txt file` section:

```
Attempting to resolve domain: used-in-tests.carbontxt.org
Trying a DNS delegated lookup for domain used-in-tests.carbontxt.org
Checking if a carbon.txt file is reachable at https://used-in-tests.carbontxt.org/carbon.txt
New Carbon text file found at: https://used-in-tests.carbontxt.org/carbon.txt
Carbon.txt file parsed as valid TOML.
Parsed TOML was recognised as valid Carbon.txt file.

✅ Carbon.txt file syntax is valid!

-------


CarbonTxtFile(upstream=Upstream(providers=[]), org=Organisation(disclosures=[Disclosure(domain='used-in-tests.carbontxt.org', doc_type='sustainability-page', url='https://used-in-tests.carbontxt.org/our-climate-record')]))
-------

Results of processing linked documents in the carbon.txt file:

{'carbon_txt_check_online': [{'url': 'https://used-in-tests.carbontxt.org/our-climate-record', 'file_online': True}]}
```

----


## Publishing external, public plugins for others to use

Internal plugins are useful for when you want to extend the validator to meet needs that only you have.

The Carbon.txt validator plugin system, pluggy, is designed to support the creation of plugins so that if you have some code that might be useful to others, then you can publish it to a publicly accessibly repository like PyPi, for others to easily use in their projects.

If you have already made an internal only plugin the process is not that different. You use almost the same actual python code to define how your plugin works when called, but you because you are making a publicly available, _external_ plugin, you need two extra things:

1. a file that describes how your plugin is to consumed in projects, called a `pyproject.toml` file
2. a folder stucture that follows conventions for publishing python packages, that a number of tools can autogenerate for you. For this example, we use `uv`.

We'll cover the `pyproject.toml` file first to explain what goes in it, and then how to generate a package that can be published to a repository like Pypi

### Creating our `pyproject.toml` file

This file does not need to be very large, and we'll cover each of the three sections below after presenting the full file:


```toml
[project]
name = "carbon-txt-check-online"
version = "0.0.1"
description = "A demonstration carbon.txt plugin that checks whether linked documents in a carbon.txt file are still online."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["httpx", "carbon-txt"]

[project.entry-points.carbon_txt]
check_online = "carbon_txt_check_online"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Add the info for your "project" section

We'll briefly cover each element one by one in the project section, but remmember, more detailed guidance is [available on the page published by Pypa, Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/):

- `name`  - your project needs a name. For it to be recognised as a plugin for the carbon.txt validator it needs to begin with `carbon-txt`, like `carbon-txt-check-online` for example.
- `version` - you'll need a version identifier so that people downloading your published project know which version do download
- `description` - Yup, you project will be easier to use if you descrtibe what it does. For our `carbon-txt-check-online`, plugin, we have _A demonstration carbon.txt plugin that checks whether linked documents in a carbon.txt file are still online._
- `readme` - what will be shown as the content when you publish it for others to download from somewhere like Pypi. This defaults to the project `README.md` file
- `requires-python`- which versions of python you support. Python 3.11 or 3.12 are both supported, but if you wanted to only support python 3.12, you would use `">=3.12"`
- `dependencies` - which other projects this relies on. In our exmaple, we are extending the carbon.txt validator which is identified as `carbon-txt`, and we are making HTTP requests, so we use the helpful `httpx` library. We use a simple list like so: `["httpx", "carbon-txt"]`

Now that we've covered this key points the text below should make some sense:

```toml
[project]
name = "carbon-txt-check-online"
version = "0.0.1"
description = "A demonstration carbon.txt plugin that checks whether linked documents in a carbon.txt file are still online."
readme = "README.md"
requires-python = ">=3.12"
dependencies = ["httpx", "carbon-txt"]
```

If we install this though, how does our carbon.txt validator know to try using it? That's the next section

#### Add the entry points to be recognised as a plugin

The lines below are required for the carbon.txt validator project, identified as `carbon-txt` to use the code in this plugin.

```toml
[project.entry-points.carbon_txt]
check_online = "carbon_txt_check_online"
```

The line `[project.entry-points.carbon_txt]` is a way of flagging up that this plugin can be considered a valid entry point for the `carbon_txt` project.

Beneath it, the `carbon_txt_check_online` is the path to the python file that contains the same code we saw use in the 'internal' plugin - the different is that rather than listing a path to a directory in file system, we are listing an path to a python module, that our plugin will have been downloaded into when used in a project.

Name the first part with the par you intend to use after the `carbon-txt` prefix. If your project name is `carbon-txt-check-online`, then use `check_online` to identify this entry point.

With these two sections, we have described our project, and defined a way to signify to projects like the carbon.txt validator that it's designed to work with it.

Now need a way to actually package up the code for publishing though.

#### Add the build backend, so the project can be built and published

Ths final stanza sets out how this project should be built, when it's published. Python is a massive ecosystem, and there are various tools that take python code, then turn it into a compressed file to store on a public repository like Pypi. The oen below is the default and simplest one, and for most cases it should be fine, so we use. You don't need to understand what hatchling is, or really what a build backend is, but if you want to know then the [Python packaging guide as some helpful info](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#declaring-the-build-backend):

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Creating our project structure

Now that we more or less know what a `pyproject.toml` file is, and that how, when combined with our existing python plugin code, shows how the code can be shared and consumed, we just need a way to create the project to hold it all.

One of the fastest ways to do this is to use a tool, `uv` to create a starter library package with the correct folder structure, with it's handy `init` command. We're creating a package to publish and for others to consume, so we pass the `--package` flag, follow by the name of our plugin:

```
uv init --package carbon-txt-check-online
```

This will create a file structure like so, with hopefully some files and folder names and you might recognise from the config earlier.

```
tree ./carbon-txt-check-online/


./carbon-txt-check-online/
├── README.md
├── pyproject.toml
├── src
│   └── carbon_txt_check_online
│       └── __init__.py
└── uv.lock

```

You replace the contents of the `pyproject.toml` with the one we ran through together, and you put the python code containing the hooks you are using in `src/carbon_txt_check_online/__init__.py`. The `uv.lock` file is created when you first run a command inside the project, to execute code, and lists all the downloaded dependencies.


```{admonition} Info
We're using `carbon-txt-check-online` for this example, but please bear in mind you'll need a different name (that one's taken for creating a demo plugin for these docs!).
```


### Running code in the external plugin

Assuming you have put the code in the correct place, if you are in that project structure, you should now be able to run `carbon-txt` validator binary, and see your plugin in use.

Run `carbon-txt plugins` to see a list of active plugins:

```
uv run carbon-txt plugins
```

Your plugin should be visible:

```
Active plugins:

 - carbon_txt_check_online
```

Similarly, you should see the plugin in use when you run the same invokation to validate a carbon.txt file online. Once again, we use `uv run` in this case to simulate running this project like it's already been built, published, downloaded and made available to your python environment.

```
uv run carbon-txt validate domain used-in-tests.carbontxt.org --plugins-dir my_plugins/
```

Our output should look something like the output below, with the extra `Results of processing linked documents in the carbon.txt file` section:

```
Attempting to resolve domain: used-in-tests.carbontxt.org
Trying a DNS delegated lookup for domain used-in-tests.carbontxt.org
Checking if a carbon.txt file is reachable at https://used-in-tests.carbontxt.org/carbon.txt
New Carbon text file found at: https://used-in-tests.carbontxt.org/carbon.txt
Carbon.txt file parsed as valid TOML.
Parsed TOML was recognised as valid Carbon.txt file.

✅ Carbon.txt file syntax is valid!

-------


CarbonTxtFile(upstream=Upstream(providers=[]), org=Organisation(disclosures=[Disclosure(domain='used-in-tests.carbontxt.org', doc_type='sustainability-page', url='https://used-in-tests.carbontxt.org/our-climate-record')]))
-------

Results of processing linked documents in the carbon.txt file:

{'carbon_txt_check_online': [{'url': 'https://used-in-tests.carbontxt.org/our-climate-record', 'file_online': True}]}
```

#### Actually publishing your package

Publishing a software package to a repository like Pypi is beyond the scope of this documentation, but the [guide on PyPa, Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/) is a helpful resource.

**A quick workaround, just to see it working**

If you don't want to jump through all these steps, and you have a created an external project that is already published on somewhere like Github, then there is a handy shortcut.

Normally if you wanted to use this new external plugin, `carbon-txt-check-online` in a different project, and you have published it to Pypi, your `pyproject.toml` file might look like this:

```toml
dependencies = [
    "some-other-dependency",
    "carbon-txt",
    "carbon-txt-check-online"
]
```

If you have uploaded the code to somewhere like Github, you can take advantage of git support in `pyproject.toml` files, to fetch it from a site like Github instead.

You can 'cheat' and point to the Github repository as a short cut, by adding a `@`, and then listing the path to the repository using the special `git+https` protocol to denote that this is a package to download from Github. If a project is accessible in your browser at this url:

```
https://github.com/thegreenwebfoundation/carbon-txt-check-online
```

Then the `git+https` link would be:

```
git+https://github.com/thegreenwebfoundation/carbon-txt-check-online.git
```

This means your list of dependencies will look like this instead:

```toml
dependencies = [
    "some-other-dependency",
    "carbon-txt",
    "carbon-txt-check-online @ git+https://github.com/thegreenwebfoundation/carbon-txt-check-online.git",
]
```

When you next try to install the dependencies in your project, the other projects will be downloaded from PyPi as usual, but because of the extra git link, the `carbon-txt-check-online` project will be downloaded from Github instead.

This is very handy for testing external plugins before 'officially' publishing them!

#### A reference external plugin

If you want to see the completed external plugin, there is a demo plugin to download and learn from on github at:

[https://github.com/thegreenwebfoundation/carbon-txt-check-online](https://github.com/thegreenwebfoundation/carbon-txt-check-online)
