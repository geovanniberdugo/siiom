from .base import *

MIDDLEWARE = [
    'siiom.middleware.LogNotAllowedHostHeaderMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'tenant_schemas.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'miembros.middleware.MiembroMiddleWare',
    'organizacional.middleware.EmpleadoMiddleWare',
]

#  Apps

SHARED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

INSTALLED_APPS = SHARED_APPS + list(set(TENANT_APPS) - set(SHARED_APPS))

#  Debug toolbar

INTERNAL_IPS = ['127.0.0.1']

# import socket
# ip = socket.gethostbyname(socket.gethostname())
# INTERNAL_IPS += [ip[:-1] + "1"]

# Email configuration

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
