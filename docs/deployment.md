# Deployment

The carbon.txt validator works as a command line tool, but also offers largely the same features over an REST-ful HTTP API, using [Django Ninja](https://django-ninja.dev/). Read on to learn about deploying the validator as a service.

## Deploying the validator

For convenience, the carbon.txt validator has a `serve` command that
spins up the default bundled Django server. This is fine for development, but
for production, we also bundle in Granian, a more performant server.

For local hosting you might run the development server like so:

```shell
# run the validator in development
carbon-txt serve
```

Ihn production, you're better off using Granian, and passing the explicit
`production` and `granian` flags. This will use the faster server, and more
secure settings suited to production.

```shell
# run in production with appropriate flags
carbon-txt serve --production --server granian
```

```{warning}
You need to set the Django SECRET KEY in production to a non default value, or the server will not work.

You can do this via setting an environment variable directly, or declaring it in a .env file in the same directory as where you are running the tool.
```

### Database configuration

The validation API requires a database, for session management, and validation request logging (see "Monitoring and gathering stats", below). By default, a sqlite database is created in the BASE_DIR of the django project (typically `$INSTALL_LOCATION/src/carbon_text/web`). This may be overridden by setting the DATABASE_URL environment variable.

On first running the `serve` command, this database will need to be initialized - you will be prompted to verify that your database connection settings are correct, and re-run with the `--migrate` flag.

### CORS support

By default, when the validator server is run, it has CORS support, and accepts
requests coming from `http://localhost:8080` and `http://127.0.0.1:8000`.

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
```

To accept responses from **all** origins set the `CORS_ALLOW_ALL_ORIGINS` to
true.

```
CORS_ALLOW_ALL_ORIGINS = True
```

## Custom django Settings

### Custom Django Settings

You can customize the Django settings used by the carbon.txt validator by using the `--django-settings` flag in the CLI. This allows you to specify a custom settings module.

For example, if you are in `/tmp` and have a custom settings file located at `/tmp/local_settings.py`, you can run the validator with your custom settings like this:

```shell
# run the validator with custom Django settings
carbon-txt serve --django-settings local_settings
```

#### Using config file in a folder

When you are using a separate settings file, you are importing a python module. So if you are importing from a settings file inside a nested folder structure, make sure that the settings module path is
a dot-separated Python import path:

```shell
# run the validator with custom Django settings file at config/settings/custom.py
carbon-txt serve --django-settings config.settings.custom
```

#### Using custom settings file to override settings

Using a custom django settings file lets you override specific settings, so if
you need to make a site CORS accessible, you might pass in a file like this:

```py
# local_config.py

from carbon_txt.web.config.settings.development import *  # noqa

# Allow connections from any domain, using the installed django-cors-headers package
# https://github.com/adamchainz/django-cors-headers#cors_allow_all_origins-bool
CORS_ALLOW_ALL_ORIGINS = True

print("Look! I accept CORS requests from everywhere.\n")
```

Then run it like this:

```
carbon-txt serve --django-settings local_config
```

You should see output like this:

```text
Using custom settings module: local_config

 ----------------

Look! I accept CORS requests from everywhere

Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 05, 2024 - 11:22:41
Django version 5.1.3, using settings 'local_config'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```


### Monitoring and tracking errors with Sentry

The Django application served by the carbon.txt validator is set up to support instrumentation with Sentry.

To activate it, you need to declare the `SENTRY_DSN`, `SENTRY_TRACE_SAMPLE_RATE` and `SENTRY_PROFILE_SAMPLE_RATE` environment variables when running the web server.

The easiest way to do this is declare them in an .env file like so:

```
# .env

SENTRY_DSN="https://LONG_ALPHANUMERIC_STRING.ingest.de.sentry.io/NUMERIC_ID"
SENTRY_TRACE_SAMPLE_RATE="1.0"
SENTRY_PROFILE_SAMPLE_RATE="1.0"
```

### Keeping secrets out of source control

The carbon.txt validator when run as a server, supports the use of `.env` (dotenv) files.

Which allows you to keep secrets in a separate file, without needing to make changes to the project codebase, or explicitly set them on the command line.

To see default values that can be override, see the `base.py` file, in `src/web/config/settings/base.py`.

#### Monitoring and gathering stats on use of the API.

When run as a server, the carbon.txt validator logs anonymous usage data about validation requests received, in order to track the uptake of the carbon.txt standard. We log the validation endpoint used (`file`, `url`, or `domain`), the domain requested and carbon.txt URL (in the case of requests to the `url` and `domain` endpoints), and whether or not the validation was succesful.

This information is saved to the application database (configured with the `DATABASE_URL` environment variable, as described above) in the table `validation_logging_ValidationLogEntry`. It is also output as an INFO message to the log, with a log name of `carbon_txt.web.validation_logging.middleware`.
