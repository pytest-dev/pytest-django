"""
This is just an intermediate plugin that sets up the django environment and 
loads the main plugin
"""

from django.core.management import setup_environ
import os
import py

def pytest_addoption(parser):
    parser.addoption('--settings', help='The Python path to a Django settings module, e.g. "myproject.settings.main". If this isn\'t provided, the DJANGO_SETTINGS_MODULE environment variable will be used.', default=None)

def pytest_configure(config):
    try:
        import settings
    except ImportError:
        pass
    else:
        setup_environ(settings)
    config_settings = config.getvalue('settings')
    if config_settings is not None:
        os.environ['DJANGO_SETTINGS_MODULE'] = config_settings
    from pytest_django import plugin
    config.pluginmanager.register(plugin)

def pytest_collect_file(path, parent):
    """
    Load all files in a tests directory as tests, following Django convention.
    
    However, we still load files such as test_urls.py in application 
    directories which are typically not tests. That might need manually
    overriding in conftest files.
    """
    if path.check(fnmatch="tests/*.py"):
        return parent.Module(path, parent=parent)

