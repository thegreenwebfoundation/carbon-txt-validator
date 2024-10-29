

# load the contents of .env into environment variables
# override by calling `just --dotenv-filename ENV_FILENAME COMMAND`
# where ENV_FILENAME is the file containing env vars you want to use instead
set dotenv-load

default:
  just --list

test *options:
  uv run pytest {{ options }}

test-watch *options:
  uv run pytest-watch -- {{ options }}


serve:
  uv run python ./src/carbon_txt_validator/web/manage.py runserver
