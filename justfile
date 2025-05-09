

# load the contents of .env into environment variables
# override by calling `just --dotenv-filename ENV_FILENAME COMMAND`
# where ENV_FILENAME is the file containing env vars you want to use instead
set dotenv-load

# list all the available commands
default:
  just --list

# invoke the cli, as if you were running `carbon-txt` after downloading the package
run-cli *options:
  uv run carbon-txt {{ options }}

# Run a command with installed python tools available via 'uv', and environment variables via 'just'
run *options:
  uv run  {{ options }}

# show the environment variables available
env:
  env

# run all the tests, with the ability to pass in options
test *options:
  uv run pytest {{ options }} --cov
# run the tests for a CI environment, generating a coverage report
ci *options:
  uv run pytest {{ options }} --cov --cov-report xml:cov.xml

# run all the tests, and re-run them when files change
test-watch *options:
  uv run pytest-watch -- {{ options }} --cov --cov-report xml:cov.xml

# serve the django app, using the django manage.py script
serve *options:
  uv run python ./src/carbon_txt/web/manage.py runserver {{ options }}

manage *options:
  uv run python ./src/carbon_txt/web/manage.py {{ options }}

# generate docs into the docs/_build/html directory
docs *options:
  uv run sphinx-build docs docs/_build/html {{ options }}

# generate docs, serve the locally over http, and update them when files change
docs-watch *options:
  uv run sphinx-autobuild docs docs/_build/html {{ options }}

# clear the dist directory, and build the project, ready for publishing
build:
  rm -rf ./dist
  uv build

# publish the built python project to pypi
publish *options: build
  uv run twine upload dist/* {{ options }}

# run marimo notebook with options
marimo *options:
  uv run marimo {{ options}}


# run a local version of a Marimo API checking notebook
marimo_api_checker:
  uv run marimo run ./docs/notebooks/notebook.py

# run a editable version of a Marimo API checking notebook
marimo_api_checker_edit:
  uv run marimo edit ./docs/notebooks/notebook.py
