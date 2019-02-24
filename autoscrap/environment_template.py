import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': '',
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': 0,
  }
}
