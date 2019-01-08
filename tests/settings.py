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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_POSTGRES", "naivedatetimefield"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_POSTGRES", 'postgres'),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_POSTGRES", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_POSTGRES", ""),
    }
}

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
