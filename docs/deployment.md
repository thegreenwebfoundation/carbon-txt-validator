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
carbon-txt-validator serve
```

Ihn production, you're better off using Granian, and passing the explicit
`production` and `granian` flags. This will use the faster server, and more
secure settings suited to production.

```shell
# run in production with appropriate flags
carbon-txt-validator serve --production --server granian
```

```{warning}
You need to set the Django SECRET KEY in production to a non default value, or the server will not work.

You can do this via setting an environment variable directly, or declaring it in a .env file in the same directory as where you are running the tool.
```
