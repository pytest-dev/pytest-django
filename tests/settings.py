DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/test'
    }
}

ROOT_URLCONF = 'tests.urls'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'tests.app',
]

STATIC_URL = '/static/'
SECRET_KEY = 'foobar'

SITE_ID = 1234  # Needed for 1.3 compatibility
