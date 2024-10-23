# Carbon.txt validator

This validator reads carbon.txt files, and validates them against a spec defined on http://carbontxt.org.




# Usage

## With the CLI

Run a validation against a given domain, or file, say if the file is valid TOML, and it confirms to the carbon.txt spec

```shell
# parse the carbon.txt file on default paths on some-domain.com
carbontxt validate domain some-domain.com

# parse a remote file available at https://somedomain.com/path-to-carbon.txt
carbontxt validate file https://somedomain.com/path-to-carbon.txt

# parse a local file ./path-to-file.com
carbontxt validate file ./path-to-file.com

# pipe the contents of a file into the file validation command as part of a pipeline
cat ./path-to-file.com | carbontxt validate file

```

## With the HTTP API

(Coming up next)
