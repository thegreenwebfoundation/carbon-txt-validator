# Usage

```{admonition} Info
:class: info
Note: this content may be a candidate for placing the [developers.thegreenwebfoundation.org website](https://developers.thegreenwebfoundation.org).
If we do this, we'd replace this page with a short para and link to it there.
```

## Using the carbon.txt validator in python

### Validating carbon.txt files from python

You can use the carbon.txt validator in python by importing and instantiating the CarbonTxtValidator class:

```python

from carbon_txt.validators import CarbonTxtValidator

validator = CarbonTxtValidator()
```

This validator object can be used to validate a given domain, URL, or the contents of a carbon.txt file as a string. Each of these methods returns a `ValidationResult` object, which exposes `logs`, any `exceptions` encountered, an optional `result` containing the parsed `CarbonTxtFile`, and an optional `url` of the parsed document (if a domain or URL was validated).

#### Find and parse a carbon.txt file for a given domain

A key idea behind carbon.txt is that it you shouldn't need to know where a carbon.txt file is on a domain to access it - there should be conventions to follow to find the file in a series of predictable places. We can perform this lookup and validate the found file, using the `validate_domain` method:

```python

validator.validate_domain("carbontxt.org")
#=> ValidationResult

```

#### Parse a carbon.txt file available at a specific URL

We can also specify the full URL to a given carbon.txt file for validation:

```python

validator.validate_url("https://thegreenwebfoundation.org/carbon.txt")
#=> ValidationResult

```

#### Parse a TOML string as a carbon.txt file

Finally, we can specify the contents of a carbon.txt file as a string, and validate that:

```python
contents = """
version = "0.4"
last_updated = "2025-01-01"

[org]
disclosures = [
    { doc_type='web-page', url='https://example.com/sustainability-policy' },
]
"""

validator.validate_contents(contents)
#=> ValidationResult

```

### Building carbon.txt files from python

We can also create carbon.txt files programatically, using the `build_from_dict` helper function:

```python

from carbon_txt import build_from_dict

data = {
    "org": {
        "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
    },
    "upstream": {
        "services": [
            {"domain": "example.com", "service_type": "virtual-private-servers"}
        ]
    },
}

build_from_dict(data)
#=> CarbonTxtFile
```

This method will automatically validate the contents of the carbon.txt file and raise a `pydantic.ValidationError` if any of the data is invalid. By default, it validates against the lastest version of the carbon.txt syntax, but will use the `version` key of the dictionary to select the correct syntax version to validate against.

If you do not specify a `last_updated` property, the current date will be specified by default. If you wish to omit this, you can provide an explicit `None` value as the `last_updated` date.


### Generating a carbon.txt file in TOML format

Any `CarbonTxtFile` object can be serialized as TOML, either by calling its `to_toml` method, which returns a TOML formatted string, or its `save_toml` method to save it to a given path:

```python

from carbon_txt import build_from_dict

data = {
    "org": {
        "disclosures": [{"url": "https://www.example.com", "doc_type": "web-page"}]
    },
    "upstream": {
        "services": [
            {"domain": "example.com", "service_type": "virtual-private-servers"}
        ]
    },
}

file = build_from_dict(data)

file.to_toml()
#=> string with contents of TOML file

file.save_toml("/tmp/carbon.txt")
#=> saves the TOML file to the given path

```

Both these methods take an optional `header_comment` keyword argument, which will prepend a comment in the generated TOML. This is useful if you want to add a note specifying which domain the carbon.txt has been generated for, for instance:

```python

file.save_toml("/tmp/carbon.txt", header_comment="This carbon.txt file was generated automatically for the domain example.com")

```


## Using the carbon.txt validator on the commandline

The carbon.txt validator is designed to work both as a command line tool, and as a HTTP server. Once installed, run the `carbon-txt` binary by itself to see the commands available:

```
carbon-txt
```

You should see output like below:

```
Usage: carbon-txt [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion  Install completion for the current shell.                                          │
│ --show-completion     Show completion for the current shell, to copy it or customize the installation.   │
│ --help                Show this message and exit.                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────╮
│ schema     Generate a JSON Schema representation of a carbon.txt file for validation                     │
│ serve      Run the carbon.txt validator web server                                                       │
│ validate   Validate carbon.txt files, either online, or locally.                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Validating files on the command line

#### Find and parse a carbon.txt file for a given domain:

A key idea behind carbon.txt is that it you shouldn't need to know where a carbon.txt file is on a domain to access it - there should be conventions to follow to find the file in a series of predictable places.

This is inspired by the [`.well-known`](https://en.wikipedia.org/wiki/Well-known_URI) URI convention, as well as other DNS based ways to discover relevant files for a given domain.

```shell
carbon-txt validate domain some-domain.com
```

#### Parse a remote carbon.txt file available at a specific URL

When testing out a file it's useful to be able to specify where to try downloading a file from. This is useful for troubleshooting, or otherwise testing out lookups

```shell
carbon-txt validate file https://somedomain.com/path-to-carbon.txt
```


#### Parse a local carbon.txt file

You can read a file on your local file system, to avoid needing to upload the file somewhere before trying to read, or when testing out data pipelines.

```shell
carbon-txt validate file ./path-to-file.txt
```


#### pipe the contents of a file into the file validation command as part of a pipeline

The carbon.txt validator tries to follow the [Command Line Interface Guidelines on clig.dev](https://clig.dev), on making it possible to build composable pipelines.

You can pipe a file into the carbon.txt validator to parse it:

```shell
cat ./path-to-file.com | carbon-txt validate file
```


#### Using the carbon.txt validator as a server

Finally, almost all of the functions of the carbon.txt validator are available over an HTTP API too. Run `carbon-txt serve` to start an API server, with OpenAPI compliant documentation of each endpoint:


```shell
carbon-txt serve
```
