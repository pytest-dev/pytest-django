from django.core.handlers.wsgi import WSGIRequest
from django.test.client import RequestFactory as VanillaRequestFactory
from django.test.client import FakePayload


class PytestDjangoRequestFactory(VanillaRequestFactory):
    """
    Based on Django 1.3's RequestFactory, but fixes an issue that causes an
    error to be thrown when creating a WSGIRequest instance with a plain call
    to RequestFactory.rf().

    This issue is fixed in Django 1.4, so this class will be unnecessary when
    support for Django 1.3 is dropped.

    https://code.djangoproject.com/ticket/15898

    Incorporates code from https://code.djangoproject.com/changeset/16933.
    """
    def request(self, **request):
        environ = {
            'HTTP_COOKIE': self.cookies.output(header='', sep='; '),
            'PATH_INFO': str('/'),
            'REMOTE_ADDR': str('127.0.0.1'),
            'REQUEST_METHOD': str('GET'),
            'SCRIPT_NAME': str(''),
            'SERVER_NAME': str('testserver'),
            'SERVER_PORT': str('80'),
            'SERVER_PROTOCOL': str('HTTP/1.1'),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': str('http'),
            'wsgi.input': FakePayload(b''),
            'wsgi.errors': self.errors,
            'wsgi.multiprocess': True,
            'wsgi.multithread': False,
            'wsgi.run_once': False,
        }
        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)

try:
    VanillaRequestFactory().request()
    RequestFactory = VanillaRequestFactory
except KeyError:
    RequestFactory = PytestDjangoRequestFactory
