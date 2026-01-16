from .base import *  # noqa
import os

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = os.environ.get("DEBUG", "False")

# STATIC
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
