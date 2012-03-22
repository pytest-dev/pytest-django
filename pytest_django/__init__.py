"""
This is just an intermediate plugin that sets up the django environment and
loads the main plugin
"""

import os

SETTINGS_DESC = """
The Python path to a Django settings module,
e.g. "myproject.settings.main". If this isn't provided,
django_settings_module must be set in the ini file.
""".strip()


def pytest_addoption(parser):
    group = parser.getgroup("django", "run tests for a Django application")
    group.addoption('--settings', help=SETTINGS_DESC, default=None)
    parser.addini("django_settings_module", SETTINGS_DESC)


def pytest_configure(config):
    config_settings = (config.getvalue('settings')
                       or config.getini("django_settings_module"))

    if not config_settings:
        return

    os.environ['DJANGO_SETTINGS_MODULE'] = config_settings

    if config.getvalue('verbose'):
        verbosity = 1
    else:
        verbosity = 0

    from pytest_django import plugin
    config.pluginmanager.register(plugin)
    config.pluginmanager.register(plugin.DjangoManager(verbosity=verbosity))
