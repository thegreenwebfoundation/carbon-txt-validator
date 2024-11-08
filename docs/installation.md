# Installation

The carbon-txt validator project uses the Pyproject format to track software library dependencies, so should work with most python tools for managing dependencies, like `pip`.

## The supported approach - using uv and just

With that in mind, the supported, 'golden path' approach is to use the `uv` tool for managing packages, and `just` for automating common tasks.

### Installing just and installing uv

You can install uv with a single one-line command on most systems:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You can also install `just` with a similar one-liner.

```shell
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to DEST
```

However, depending on your system there may be an option that integrates better with your setup - [please see the installation docs for more](https://github.com/casey/just?tab=readme-ov-file#installation).

### Developing with just

Once just and uv are set up, run `just` to see a list of tasks available for development:

```
just
```

You should see a list of tasks like this:

```
just --list
Available recipes:
    build               # clear the dist directory, and build the project, ready for publishing
    ci *options         # run the tests for a CI environment, generating a coverage report
    default             # list all the available commands
    docs *options       # generate docs into the docs/_build/html directory
    docs-watch *options # generate docs, serve the locally over http, and update them when files change
    env                 # show the environment variables available
    publish *options    # publish the built python project to pypi
    run-cli *options    # invoke the cli, as if you were running `carbon-txt` after downloading the package
    serve *options      # serve the django app, using the django manage.py script
    test *options       # run all the tests, with the ability to pass in options
    test-watch *options # run all the tests, and re-run them when files change
```

You can then run `just test` to run the tests, or to simulate running the CLI app, `just run-cli`.

This will also default to running each taks with any environment variables defined in `.env` available. you can override this by passing in a path to a custom environment file if need be:

```
just --dotenv-path ./path/to/custom.env YOUR_CHOSEN_TASK
```

### Running tests

Run `just test` for a one off invocation of pytest.

Run `just test-watch` to run pytest every time files are updated.

By default, running this will also generate a test coverage report, that can be picked up by your editor to display code that still needs test coverage ([see an example for VS code](https://github.com/ryanluker/vscode-coverage-gutters))

### Seeing and building documentation

Similarly you can build docs using `just docs` to generate the docs once, and just `docs-watch` to run a server that live updates.
