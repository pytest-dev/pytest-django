from django.core import mail
from django.db import connection
from app.models import Item
from django.conf import settings

# It doesn't matter which order all the _again methods are run, we just need 
# to check the environment remains constant.
# This is possible with some of the testdir magic, but this is a nice lazy to
# it

def test_mail():
    assert len(mail.outbox) == 0 #@UndefinedVariable
    mail.send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
    assert len(mail.outbox) == 1 #@UndefinedVariable
    m = mail.outbox[0] #@UndefinedVariable
    assert m.subject == 'subject'
    assert m.body == 'body'
    assert m.from_email == 'from@example.com'
    assert list(m.to) == ['to@example.com']

def test_mail_again():
    test_mail()

def test_database_rollback():
    assert Item.objects.count() == 0
    Item.objects.create(name='blah')
    assert Item.objects.count() == 1

def test_database_rollback_again():
    test_database_rollback()

def test_database_name():
    print connection.settings_dict
    assert connection.settings_dict['NAME'] == ':memory:'
    assert settings.DATABASE_NAME == '/tmp/test'
    
def test_transaction_support_for_sqllite():
    assert connection.settings_dict['SUPPORTS_TRANSACTIONS']
    