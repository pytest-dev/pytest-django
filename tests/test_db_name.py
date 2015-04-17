# coding: utf-8

from django import VERSION as DJANGO_VERSION

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


def test_name_sqlite():
    db_settings = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'pytest_django',
        'HOST': 'localhost',
        'USER': '',
    }
    assert _get_db_name(db_settings, None) == ':memory:'
    assert _get_db_name(db_settings, 'abc') == ':memory:'

    if DJANGO_VERSION > (1, 7):
        db_settings['TEST'] = {'NAME': 'custom_test_db'}
    else:
        db_settings['TEST_NAME'] = 'custom_test_db'
    assert _get_db_name(db_settings, None) == 'custom_test_db'
    assert _get_db_name(db_settings, 'abc') == 'custom_test_db_abc'


def test_testname():
    db_settings = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pytest_django',
        'HOST': 'localhost',
        'USER': '',
    }
    if DJANGO_VERSION > (1, 7):
        db_settings['TEST'] = {'NAME': 'test123'}
    else:
        db_settings['TEST_NAME'] = 'test123'
    assert _get_db_name(db_settings, None) == 'test123'
    assert _get_db_name(db_settings, 'abc') == 'test123_abc'
