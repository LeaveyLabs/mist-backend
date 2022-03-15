from backend.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
from decouple import config
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Any host is allowed
ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'kevinsun',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}
# TODO: Pictures
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 
MEDIA_URL = '/media/'