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
'''
Why this block? 
GITHUB_WORKFLOW env variable is only available in GitHub Actions. So in actions
we want a simple postgres docker image to be booted as a service and does all the testing there.
When we deploy to cloud the else block will work as we won't be having GITHUB_WORKFLOW env var in our deployment.
That time the db config we use DB_USER, DB_NAME, DB_PASSWORD, DB_HOST and DB_PASSWORD
which we will set in repository secret to be used in our deployment.
'''
if os.getenv('GITHUB_WORKFLOW'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'github-actions',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '5432'
        }
    }
else:
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