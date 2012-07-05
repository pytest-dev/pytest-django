from django.http import HttpRequest
from django.test.client import Client
from pytest_django.client import RequestFactory
import pytest

pytest_plugins = ['pytester']


def test_client(client):
    assert isinstance(client, Client)


def test_admin_client(admin_client):
    assert isinstance(admin_client, Client)
    assert admin_client.get('/admin-required/').content == 'You are an admin'


def test_rf(rf):
    assert isinstance(rf, RequestFactory)
    try:
        rf.request()
    except:
        pytest.fail(msg='Plain call to funcarg rf.request() throws error.')
    request = rf.get('/path/')
    assert isinstance(request, HttpRequest)
    assert request.path == '/path/'
    assert request.method == 'GET'
    request = rf.post('/submit/', {'foo': 'bar'})
    assert isinstance(request, HttpRequest)
    assert request.path == '/submit/'
    assert request.method == 'POST'
    assert request.POST['foo'] == 'bar'


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
