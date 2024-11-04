# Deployment

The carbon.txt validator works as a command line tool, but also offers largely
the same features over an RESTful HTTP API, using
[Django Ninja](https://django-ninja.dev/). Read on to learn about deploying the
validator as a service.

## Deploying the validator

For convenience, carbon.txt validator has a convenience `serve` command, that
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

```{admonition} TODO
Add support for setting new CORS ALLOWED ORIGINS in production once we deploy to production.
```
