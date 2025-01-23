# Usage

```{admonition} Info
:class: info
Note: this content may be a candidate for placing the [developers.thegreenwebfoundation.org website](https://developers.thegreenwebfoundation.org).
If we do this, we'd replace this page with a short para and link to it there.
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
