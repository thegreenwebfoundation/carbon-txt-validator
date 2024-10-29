# Carbon.txt validator

This validator reads carbon.txt files, and validates them against a spec defined
on http://carbontxt.org.

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

If you are not using a virtual environments, but running `uv`, in a project you
can run it with `uv run carbon-txt your args`

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
