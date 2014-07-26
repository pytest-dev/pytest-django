from tests.settings_base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    },
}

INSTALLED_APPS += [
    'tests.custom_user'
]

AUTH_USER_MODEL = 'custom_user.MyCustomUser'
