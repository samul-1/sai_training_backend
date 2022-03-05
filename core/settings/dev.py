from .base import *
import os

REST_FRAMEWORK = {
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # for browsable api
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",  # django-oauth-toolkit >= 1.0.0
        "rest_framework_social_oauth2.authentication.SocialAuthentication",
    ),
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'training-db-sql', 
        'USER': 'postgres', 
        'PASSWORD': os.environ.get('LOCAL_DB_PWD'),
        'HOST': '127.0.0.1', 
        'PORT': '5432',
    }
}