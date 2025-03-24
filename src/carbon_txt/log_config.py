import logging
import logging.config
import structlog

from typing import Any

# to get logging working consistently the Django webserver and the CLI
# we need to configure both:
#
# 1. structlog, for our code, AND
# 2. configure the default logging.logger libraries


class RemoveAttributesProcessor:
    """
    A tiny log processor which removes attributes from specific logs.

    django-structlog adds personally-identifying request context info to everything logged
    from within the web application, and there are occasions (eg the validation request logs)
    where we *DON'T* want this information to be logged, as the those particular logs are
    persisted for longer, or contain other data (eg domains requested for validation) which
    we *DON'T* want to be able to associate with user PII. We use this filter to remove
    them where needed!
    """

    def __init__(self, loggers: list[str], attributes: list[str]):
        """
        Args:
            - loggers: A list of names of loggers to which we want this processor to apply:
            - attributes: A list of attributes which we want to filter from the logs.

        Returns:
            - A log processing function which filters those particular attributes from
              events logged by those particular loggers.
        """
        self.loggers = loggers
        self.attributes = attributes

    def __call__(
        self, logger: logging.Logger, log_method: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        if logger is not None and logger.name in self.loggers:
            for attribute in self.attributes:
                if attribute in event_dict:
                    del event_dict[attribute]
        return event_dict


shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
    # Anonymise requested domain logs
    RemoveAttributesProcessor(
        loggers=["carbon_txt.web.validation_logging"],
        attributes=["ip", "request_id", "user_id"],
    ),
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
        "carbon_txt.web.validation_logging": {
            "level": "INFO",
        },
    },
}


# configure logging with the massive logging dict
logging.config.dictConfig(LOGGING)
