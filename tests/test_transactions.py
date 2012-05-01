from django.db import transaction

from pytest_django import transaction_test_case

from app.models import Item


def django_transactions_is_noops():
    """
    Creates an object in a transaction and issues a ROLLBACK.

    If transactions is being active, no object should be created in the
    database.

    If transactions are being NOOP:ed by Django during normal test runs,
    one object should remain after invokation.
    """

    with transaction.commit_manually():
        assert not Item.objects.exists()
        Item.objects.create(name='a')
        assert Item.objects.exists()
        transaction.rollback()

    # If a object still exists, no real rollback took place, and transactions
    # are just NOOPs
    return Item.objects.exists()


@transaction_test_case
def test_transaction_test_case():
    assert not django_transactions_is_noops()


@transaction_test_case
def test_transaction_test_case_again():
    test_transaction_test_case()


def test_normal_test_case():
    assert django_transactions_is_noops()


def test_normal_test_case_again():
    test_normal_test_case()
