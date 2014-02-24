# coding: utf-8

from pytest_django.db_reuse import _get_db_name


def test_name():
    db_settings = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pytest_django',
        'TEST_NAME': '',
        'HOST': 'localhost',
        'USER': '',
    }
    assert _get_db_name(db_settings, None) == 'test_pytest_django'
    assert _get_db_name(db_settings, 'abc') == 'test_pytest_django_abc'


def test_testname():
    db_settings = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pytest_django',
        'TEST_NAME': 'test123',
        'HOST': 'localhost',
        'USER': '',
    }
    assert _get_db_name(db_settings, None) == 'test123'
    assert _get_db_name(db_settings, 'abc') == 'test123_abc'
