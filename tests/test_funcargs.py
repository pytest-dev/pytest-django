import pytest
from django.test.client import Client, RequestFactory

pytest_plugins = ['pytester']


def test_client(client):
    assert isinstance(client, Client)


@pytest.mark.djangodb
def test_admin_client(admin_client):
    assert isinstance(admin_client, Client)
    assert admin_client.get('/admin-required/').content == 'You are an admin'


def test_rf(rf):
    assert isinstance(rf, RequestFactory)


# These tests should really be done with a testdir, but setting up the Django
# environment within the temporary tests is a right pain
def test_settings(settings):
    assert settings.DEFAULT_FROM_EMAIL != 'somethingdifferent@example.com', settings.DEFAULT_FROM_EMAIL
    settings.DEFAULT_FROM_EMAIL = 'somethingdifferent@example.com'
    assert settings.DEFAULT_FROM_EMAIL == 'somethingdifferent@example.com'
    from django.conf import settings as real_settings
    assert real_settings.DEFAULT_FROM_EMAIL == 'somethingdifferent@example.com'


def test_settings_again(settings):
    test_settings(settings)
