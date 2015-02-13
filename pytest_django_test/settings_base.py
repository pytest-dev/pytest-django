import os

ROOT_URLCONF = 'pytest_django_test.urls'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'pytest_django_test.app',
]

STATIC_URL = '/static/'
SECRET_KEY = 'foobar'

SITE_ID = 1234  # Needed for 1.3 compatibility

# Used to construct unique test database names to allow detox to run multiple
# versions at the same time
uid = os.getenv('UID', '')

if uid:
    db_suffix = '_%s' % uid
else:
    db_suffix = ''

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
