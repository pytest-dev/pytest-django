import copy

from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory, Client


def pytest_funcarg__client(request):
    """
    Returns a Django test client instance.
    """
    return Client()


def pytest_funcarg__admin_client(request):
    """
    Returns a Django test client logged in as an admin user.
    """

    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com',
                                        'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()

    client = Client()
    client.login(username='admin', password='password')

    return client


def pytest_funcarg__rf(request):
    """
    Returns a RequestFactory instance.
    """
    return RequestFactory()


def pytest_funcarg__settings(request):
    """
    Returns a Django settings object that restores any changes after the test
    has been run.
    """
    old_settings = copy.deepcopy(settings)

    def restore_settings():
        for setting in dir(old_settings):
            if setting == setting.upper():
                setattr(settings, setting, getattr(old_settings, setting))
    request.addfinalizer(restore_settings)
    return settings
