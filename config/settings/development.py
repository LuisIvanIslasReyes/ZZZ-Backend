"""
Development settings
"""
from .base import *

DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
