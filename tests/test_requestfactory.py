from django.http import HttpRequest
from pytest_django.client import RequestFactory

def test_get():
    request = RequestFactory().get('/path/')
    assert isinstance(request, HttpRequest)
    assert request.path == '/path/'
    assert request.method == 'GET'

def test_post():
    request = RequestFactory().post('/submit/', {'foo': 'bar'})
    assert isinstance(request, HttpRequest)
    assert request.path == '/submit/'
    assert request.method == 'POST'
    assert request.POST['foo'] == 'bar'
