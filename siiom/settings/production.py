from .base import *

DEBUG = False

#  Ssl configuration

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email configuration

EMAIL_HOST_PASSWORD = ENV('EMAIL_HOST_PASSWORD')
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = ENV('EMAIL_HOST_USER')
EMAIL_USE_TLS = True
EMAIL_PORT = '587'

# Logging

LOGGING['loggers']['django'] = {
    'level': 'WARNING',
    'handlers': ['console'],
    'propagate': False,
}

LOGGING['loggers']['siiom'] = {
    'level': 'INFO',
    'handlers': ['console'],
    'propagate': False,
}
