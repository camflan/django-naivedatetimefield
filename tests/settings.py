import os

SECRET_KEY = "fake-key"
INSTALLED_APPS = ["tests"]

AVAILABLE_DATABASES = {
    "sqlite": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TIME_ZONE": "America/Chicago",
    },
    "postgres": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_POSTGRES", "naivedatetimefield"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_POSTGRES", "postgres"),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_POSTGRES", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_POSTGRES", ""),
    },
    "mysql": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_MYSQL", "naivedatetimefield"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_MYSQL", "root"),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_MYSQL", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_MYSQL", ""),
        "TIME_ZONE": "America/Chicago",
    },
}

DATABASES = {"default": AVAILABLE_DATABASES[os.environ.get("DB", "postgres")]}

DEBUG = True

USE_TZ = True

TIME_ZONE = "Australia/Perth"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
