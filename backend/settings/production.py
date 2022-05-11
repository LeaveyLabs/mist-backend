from backend.settings.base import *

DEBUG = False

ALLOWED_HOSTS = ['https://mist-backend.herokuapp.com']

CORS_ALLOWED_ORIGINS = [
    'https://mist-backend.herokuapp.com',
]

import django_heroku
django_heroku.settings(locals())

import dj_database_url
DATABASES = {'default': dj_database_url.config(conn_max_age=600)}

# TODO: Pictures
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 
MEDIA_URL = '/media/'

import os
from decouple import config

os.environ.setdefault('AWS_ACCESS_KEY_ID', config('AWS_ACCESS_KEY_ID'))
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', config('AWS_SECRET_ACCESS_KEY'))
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_REGION_NAME = "us-west-1"
AWS_STORAGE_BUCKET_NAME = "mistbucket"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'