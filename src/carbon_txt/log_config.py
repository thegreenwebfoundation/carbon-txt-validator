import logging
import logging.config
import structlog

# to get logging working consistently the Django webserver and the CLI
# we need to configure both:
#
# 1. structlog, for our code, AND
# 2. configure the default logging.logger libraries


shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# https://www.structlog.org/en/stable/standard-library.html
# configure here sets up our structlog logger, so we can
# use structlog.get_logger() to get a logger that logs the way we want
structlog.configure(
    processors=shared_processors
    + [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],  # type: ignore
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
    # we can use the make_filtering_bound_logger method to filter out
    # log messages before they make it to a processor
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
)

logger = structlog.get_logger()


# We now need to configure the default logging that uses logging.logger,
# so that `logging.getLogger()` follows the same kinds of formatting rules.
# We set up our LOGGING dict, and then load it in wuth the dictConfig() method

# we define how django loggers should work here too, as we Django needs to load
# this in too, upon setup

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": shared_processors,
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
            # this is required to add the log levels and timestamps
            "foreign_pre_chain": shared_processors,
        },
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(
                key_order=["timestamp", "level", "event", "logger"]
            ),
            "foreign_pre_chain": shared_processors,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
        },
        "nullhandler": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        # set our default logger
        "root": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "level": "INFO",
            "handlers": ["console"],
        },
        # if we have django_structlog logging requests, then django
        # server can be seen as redundant. So we use the nullhandler
        "django.server": {
            "formatter": "plain_console",
            "level": "INFO",
            "handlers": ["nullhandler"],
        },
        "django_structlog": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "django.utils.autoreload": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "httpx": {
            "level": "WARNING",
        },
        "httpcore": {
            "level": "WARNING",
        },
        "carbon_txt": {
            "level": "WARNING",
        },
    },
}


# configure logging with the massive logging dict
logging.config.dictConfig(LOGGING)
