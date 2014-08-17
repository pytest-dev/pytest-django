from __future__ import with_statement

import pytest
from django.core import mail
from django.db import connection

from pytest_django_test.app.models import Item


# It doesn't matter which order all the _again methods are run, we just need
# to check the environment remains constant.
# This is possible with some of the testdir magic, but this is a nice lazy to
# it


def test_mail():
    assert len(mail.outbox) == 0
    mail.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert m.subject == 'subject'
    assert m.body == 'body'
    assert m.from_email == 'from@example.com'
    assert list(m.to) == ['to@example.com']


def test_mail_again():
    test_mail()


@pytest.mark.django_db
def test_database_rollback():
    assert Item.objects.count() == 0
    Item.objects.create(name='blah')
    assert Item.objects.count() == 1


@pytest.mark.django_db
def test_database_rollback_again():
    test_database_rollback()


def test_database_name():
    name = connection.settings_dict['NAME']
    assert name == ':memory:' or name.startswith('test_')


def test_database_noaccess():
    with pytest.raises(pytest.fail.Exception):
        Item.objects.count()
