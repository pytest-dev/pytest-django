import pytest


def transaction_test_case(*args, **kwargs):
    raise pytest.UsageError('transaction_test_case has been deprecated: use '
                            'pytest.mark.django_db(transaction=True) ')


def pytest_namespace():
    def load_fixture(*args, **kwargs):
        raise pytest.UsageError('pytest.load_fixture has been deprecated')

    def urls(*args, **kwargs):
        raise pytest.UsageError('pytest.urls has been deprecated: use '
                                'pytest.mark.urls instead')

    return {'load_fixture': load_fixture, 'urls': urls}
