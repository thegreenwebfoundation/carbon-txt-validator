

# load the contents of .env into environment variables
# override by calling `just --dotenv-filename ENV_FILENAME COMMAND`
# where ENV_FILENAME is the file containing env vars you want to use instead
set dotenv-load

# list all the available commands
default:
  just --list

# run all the tests, with the ability to pass in options
test *options:
  uv run pytest {{ options }}

# run all the tests, and re-run them when files change
test-watch *options:
  uv run pytest-watch -- {{ options }}

# serve the django app, using the django manage.py script
serve *options:
  uv run python ./src/carbon_txt/web/manage.py runserver {{ options }}

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

publish *options: build
  uv run twine upload dist/* {{ options }}
