from .settings_base import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pytest_django' + db_suffix,  # noqa
        'HOST': 'localhost',
        'USER': 'root',
        'OPTIONS': {
            'init_command': 'SET storage_engine=InnoDB'
        }
    },
}
