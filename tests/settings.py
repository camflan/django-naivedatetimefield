import os

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "naivedatetimefield",

    "tests",
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

MIDDLEWARE = MIDDLEWARE_CLASSES

AVAILABLE_DATABASES = {
    "sqlite": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "postgres": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_POSTGRES", "naivedatetimefield"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_POSTGRES", 'postgres'),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_POSTGRES", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_POSTGRES", ""),
    },
    "mysql": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_MYSQL", "naivedatetimefield"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_MYSQL", 'root'),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_MYSQL", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_MYSQL", ""),
    },
}

DATABASES = {"default": AVAILABLE_DATABASES[os.environ.get("DB", "postgres")]}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'naivedatetimefield_testing_cache',
    }
}

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

DEBUG = True

USE_TZ = True
TIME_ZONE = 'America/Chicago'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGGING = {
    'disable_existing_loggers': False,
    'version': 1,
    'handlers': {
        'console': {
            # logging handler that outputs log messages to terminal
            'class': 'logging.StreamHandler',
            'level': 'DEBUG', # message level to be written to console
        },
    },
    'loggers': {
        '': {
            # this sets root level logger to log debug and higher level
            # logs to console. All other loggers inherit settings from
            # root level logger.
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False, # this tells logger to send logging message
                                # to its parent (will send if set to True)
        },
        'django.db': {
            # django also has database level logging
        },
    },
}
