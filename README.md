# Welcome
**This repository holds the code that builds our carbon.txt validator. This validator reads carbon.txt files and validates them against a spec defined on http://carbontxt.org.builds. We use it to host active development of this validator and to manage/discuss technical issues.**

You can see a working implementation of this validator service at [https://carbontxt.org/tools](https://carbontxt.org/tools).

If you would like to collaborate with us on improving the way this validator works and how it can be extended for use by others through the plugin system, this is the place for you! You can head to [this repo's issues section](https://github.com/thegreenwebfoundation/carbon-txt-validator/issues) to share your ideas, or find [basic usage details](#usage) at the end of this readme.

If you've come here looking for something else, hop to the "[I came looking for](#looking-for)" section.



## Overview - what is the carbon.txt project?

carbon.txt makes sustainability data easier to discover and use on the web. Carbon.txt is a single place to look on any domain – */carbon.txt* – for public, machine-readable, sustainability data relating to that company.

It’s a web-first, connect not collect style approach, of most benefit to those interested in scraping the structured data companies have to publish according to national laws. Designed to be extended by default, we see carbon.txt becoming essential infrastructure for sustainability data services crunching available numbers and sharing the stories it can tell.

[Visit the Green Web Foundation website for a full overview](https://www.thegreenwebfoundation.org/tools/carbon-txt/).

<a id="looking-for"></a>
## I came looking for...

### An overview of the carbon.txt project 
[See the Green Web Foundation website](https://www.thegreenwebfoundation.org/tools/carbon-txt/).

<a id="docs"></a>
### Technical documentation
There are a number of places where we hold technical documentation for this project. The best starting point to find what you're looking for is on [https://carbontxt.org/](https://carbontxt.org/).

The [issues sections](#issues) of our main github repos is also a great source of help. You might find someone has already asked for help on the same issue and you’ll find an answer. We appreciate those that take the time to create public issues for this reason, it may help someone who encounters something similar after you.

<a id="issues"></a>
### A place to raise a technical issue with the project

Technical issues can cover a broad range of things. We take this to mean:

- Reporting a bug or something not working as you expect.
- Suggesting a new feature or improvement that could be made.

Our project GitHub repos are generally the best place to raise technical issues like these. We have a number of repos that cover different aspects of our project. Here’s a summary of those and a link to the relevant issues part of that repo:

Extending the carbon.txt approach such as running your own validator service or creating plugins (this repository) - https://github.com/thegreenwebfoundation/carbon-txt-validator/issues

Using the carbon.txt validator tools on our public website - https://github.com/thegreenwebfoundation/carbon-txt-site/issues

Developing the carbon.txt syntax and specification - https://github.com/thegreenwebfoundation/carbon.txt/issues

If you are unsure of the best repo for your issue, please just make your best guess. We'll move it if we think it necessary.

### Answers to questions
If you need help with a specific technical issue, our [technical documentation](#docs) is there to help. If you need can't find what you're looking for consider raising [an issue](#issues). 

If that doesn't feel right for any reason or you would value a private conversation, please use the [Green Web Foundation support form](https://www.thegreenwebfoundation.org/support-form/).

### Ways to contribute to existing ideas
We *really* welcome community feedback on ideas we are looking to move forward, or ideas that have come from others in the community. The best place for this is in the [issues section](#issues) of our three main github repositories as explained above. 

### Ways to collaborate, donate or fund this project
We are always open for discussions about how people can contribute back to the development and success of this tool through collaboration or financial donations. Please use the [Green Web Foundation support form](https://www.thegreenwebfoundation.org/support-form/) to let us know what you’d like to chat about.


<a id="usage"></a>
# Usage

## With the CLI

Run a validation against a given domain, or file, say if the file is valid TOML,
and it confirms to the carbon.txt spec.

The following commands assume you are working in a virtual environment:

```shell
# parse the carbon.txt file on default paths on some-domain.com
carbon-txt validate domain some-domain.com

# parse a remote file available at https://somedomain.com/path-to-carbon.txt
carbon-txt validate file https://somedomain.com/path-to-carbon.txt

# parse a local file ./path-to-file.com
carbon-txt validate file ./path-to-file.com

# pipe the contents of a file into the file validation command as part of a pipeline
cat ./path-to-file.com | carbontxt validate file
```

### Using UV

If you are not using virtual environments directly, you can use it with
[uv](https://docs.astral.sh/uv/), which is the recommended way to run the
project.

Add carbon-txt to a project with `uv add`:

```
uv add carbon-txt
```

You can now run the command line tool with `uv run carbon-txt`

### Running outside a project

If you have uv installed, you can run the command line tool like so:

```
# check a file
uv tool run carbon-txt validate ./path/to/file

# run a server
uv tool run carbon-txt serve
```

This will download the latest published version from pypi and run the
corresponding CLI command

## With the HTTP API

You can also validate carbon.txt files sent over an HTTP API.

```shell
# run the carbon-txt validator as a server using the default django server. Not for production
carbon-txt serve
```

For production, [Granian](https://github.com/emmett-framework/granian), a
performant webserver is bundled. Pass the flag `--server granian` to use it.

```shell
# run the carbon-txt validator as a server using the production granian server
carbon-txt serve --server granian
```
