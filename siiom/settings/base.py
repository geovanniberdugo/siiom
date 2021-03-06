"""
Django settings for siiom project.

Generated by 'django-admin startproject' using Django 1.8.17.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import re
import environ
from django.contrib.messages import constants as messages


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = environ.Path(__file__) - 3
ENV = environ.Env()
ENV.read_env()


# Make this unique, and don't share it with anybody.
SECRET_KEY = ENV('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['.localhost']
ALLOWED_HOSTS = ENV.list('ALLOWED_HOSTS', default=['.localhost', '*'])

LOGIN_URL = '/iniciar_sesion/'

# Application definition

SHARED_APPS = [
    'tenant_schemas',

    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'django.forms',

    'waffle',
    'import_export',

    'clientes',  # Maneja las iglesias
]

TENANT_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.contenttypes',

    'waffle',
    'treebeard',
    'import_export',

    'pqr',
    'common',
    'grupos',
    'compras',
    'miembros',
    'reportes',
    'encuentros',
    'consolidacion',
    'organizacional',
    'gestion_documental',
    'instituto',
    'feed'
]

INSTALLED_APPS = SHARED_APPS + list(set(TENANT_APPS) - set(SHARED_APPS))

TENANT_MODEL = 'clientes.Iglesia'

MIDDLEWARE = [
    'siiom.middleware.LogNotAllowedHostHeaderMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'tenant_schemas.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'miembros.middleware.MiembroMiddleWare',
    'organizacional.middleware.EmpleadoMiddleWare',
]

ROOT_URLCONF = 'siiom.urls'

IGNORABLE_404_URLS = [re.compile(r'^/robots\.txt$'), re.compile(r'^/favicon\.ico$')]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.media',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'context_processors.siiom_context_processor',
            ],
        },
    },
]

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

SITE_ID = 1

WSGI_APPLICATION = 'siiom.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_ROUTERS = ('tenant_schemas.routers.TenantSyncRouter',)

DATABASES = {
    'default': ENV.db(engine='tenant_schemas.postgresql_backend')
}

# Cache

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'KEY_FUNCTION': 'tenant_schemas.cache.make_key'
    }
}
# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-CO'

USE_I18N = True

USE_L10N = True

USE_TZ = False

TIME_INPUT_FORMATS = (
    '%H:%M:%S',     # '14:30:59'
    '%H:%M:%S.%f',  # '14:30:59.000200'
    '%H:%M',        # '14:30'
    '%I:%M %p',     # '06:30 AM'
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR('../static')
STATICFILES_DIRS = (BASE_DIR('static'),)

# Media files

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR('../media')
DEFAULT_FILE_STORAGE = 'siiom.storage.TenantFileSystemStorage'
FILE_UPLOAD_PERMISSIONS = 0o644

AUTH_PASSWORD_VALIDATORS = []

# Email configuration

DEFAULT_FROM_EMAIL = 'SIIOM <noreply@siiom.net>'

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'tenant_context': {
            '()': 'tenant_schemas.log.TenantContextFilter'
        },
    },
    'formatters': {
        'tenant_context': {
            'format': '[%(schema_name)s:%(domain_url)s] %(levelname)-7s %(asctime)s %(module)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['tenant_context'],
            'class': 'logging.StreamHandler',
            'formatter': 'tenant_context',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
        'siiom': {
            'handlers': ['console'],
            'propagate': False
        }
    },
}

AUTHENTICATION_BACKENDS = (
    'miembros.backends.EmailAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Google analytics
ANALYTICS = ENV.bool('ANALYTICS', default=False)

# Messages

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}