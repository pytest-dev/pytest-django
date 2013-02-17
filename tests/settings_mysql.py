from tests.settings_base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pytest_django',
        'HOST': 'localhost',
        'USER': 'root',
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB'
        }
    },
}
