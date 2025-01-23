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

from carbon_txt.plugins import hookimpl

import httpx

@hookimpl
def process_document(document):

    # we send a HEAD request, as we are not trying to download the file
    # and check the contents, just see that it's reachable
    response = httpx.head(document.url, follow_redirects=True)

    if response.status_code == 200:
        file_online = True
    else:
        file_online = False

    results = {
        "domain": document.domain,
        "url": document.url,
        "file_online": file_online
    }
    return results

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

[{'domain': 'used-in-tests.carbontxt.org', 'url': 'https://used-in-tests.carbontxt.org/our-climate-record', 'file_online': True}]
```
