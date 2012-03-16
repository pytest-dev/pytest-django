"""
This is just an intermediate plugin that sets up the django environment and
loads the main plugin
"""

import os


def pytest_addoption(parser):
    parser.addoption('--settings', help='The Python path to a Django settings module, e.g. "myproject.settings.main". If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment variable will be used.', default=None)
    parser.addoption('--noinput', help='Tells Django not to ask for any user input.', action='store_true', default=False)


def pytest_configure(config):
    config_settings = config.getvalue('settings')
    if config_settings is not None:
        os.environ['DJANGO_SETTINGS_MODULE'] = config_settings

    from pytest_django import plugin
    config.pluginmanager.register(plugin)
