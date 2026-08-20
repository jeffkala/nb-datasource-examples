"""Nautobot development configuration file."""

import os

from nautobot.core.settings import *  # noqa: F403  # pylint: disable=wildcard-import,unused-wildcard-import,import-error

SECRET_KEY = "NOTASECRET"  # noqa: S105

DATABASES = {
    "default": {
        "NAME": os.getenv("NAUTOBOT_DB_NAME", "nautobot"),
        "USER": os.getenv("NAUTOBOT_DB_USER", "nautobot"),
        "PASSWORD": os.getenv("NAUTOBOT_DB_PASSWORD", "nautobot"),  # noqa: S105
        "HOST": os.getenv("NAUTOBOT_DB_HOST", "localhost"),
        "PORT": os.getenv("NAUTOBOT_DB_PORT", "5432"),
        "ENGINE": "django.db.backends.postgresql",
    }
}
