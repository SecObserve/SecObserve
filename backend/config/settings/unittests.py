from .prod import *  # noqa

# Basically disable throttling for unit tests
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000/second",
    "user": "1000/second",
}


class DisableMigrations:
    """
    Reports every app as having no migrations, so that database schemas are created directly
    from the models. Running all migrations takes a considerable amount of time and is done
    twice for every run of the unit tests, once for the database of the entrypoint and once
    for the database of the test runner. That the migrations result in the same schema is
    covered by the end to end tests, which start the backend with a fresh database.
    """

    def __contains__(self, item: str) -> bool:
        return True

    def __getitem__(self, item: str) -> None:
        return None


MIGRATION_MODULES = DisableMigrations()

TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": [str(ROOT_DIR / "templates")],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": True,
        },
    },
]
