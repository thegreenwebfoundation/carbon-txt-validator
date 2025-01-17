from .base import *  # noqa

INTERNAL_IPS = ["127.0.0.1"]
ALLOWED_HOSTS.extend(["127.0.0.1", "localhost"])  # noqa

WSGI_APPLICATION = "carbon_txt.web.config.wsgi.application"
ROOT_URLCONF = "carbon_txt.web.config.urls"

LOGGING["handlers"]["console"] = {  # type: ignore # noqa
    "class": "logging.StreamHandler",
    # "formatter": "key_value",
    "formatter": "plain_console",
    # "formatter": "json_formatter",
}

LOGGING["loggers"] = {  # type: ignore # noqa
    "root": {
        "handlers": ["console"],
        # make test logs much more quiet. Set this to INFO and specific loggers
        # below to DEBUG for troubleshooting
        "level": "ERROR",
        # "propagate": True,
    },
    #     "django_structlog": {
    #         # "level": "ERROR",
    #     },
    #     "httpx": {
    #         # "level": "WARNING",
    #     },
    #     "httpcore": {
    #         # "level": "INFO",
    #     },
    #     "carbon_txt": {
    #         # "level": "INFO",
    #     },
    #     "test_plugin": {
    #         # "level": "ERROR",
    #     },
}
