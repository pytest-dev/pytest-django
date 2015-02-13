import pytest
from django.test import TestCase

from pytest_django_test.app.models import Item
from pytest_django_test.compat import force_text


class TestFixtures(TestCase):
    fixtures = ['items']

    def test_fixtures(self):
        assert Item.objects.count() == 1
        assert Item.objects.get().name == 'Fixture item'

    def test_fixtures_again(self):
        """Ensure fixtures are only loaded once."""
        self.test_fixtures()


class TestSetup(TestCase):
    def setUp(self):
        """setUp should be called after starting a transaction"""
        assert Item.objects.count() == 0
        Item.objects.create(name='Some item')
        Item.objects.create(name='Some item again')

    def test_count(self):
        self.assertEqual(Item.objects.count(), 2)
        assert Item.objects.count() == 2
        Item.objects.create(name='Foo')
        self.assertEqual(Item.objects.count(), 3)

    def test_count_again(self):
        self.test_count()

    def tearDown(self):
        """tearDown should be called before rolling back the database"""
        assert Item.objects.count() == 3


class TestFixturesWithSetup(TestCase):
    fixtures = ['items']

    def setUp(self):
        assert Item.objects.count() == 1
        Item.objects.create(name='Some item')

    def test_count(self):
        assert Item.objects.count() == 2
        Item.objects.create(name='Some item again')

    def test_count_again(self):
        self.test_count()

    def tearDown(self):
        assert Item.objects.count() == 3


class TestUrls(TestCase):
    """
    Make sure overriding ``urls`` works.
    """
    urls = 'pytest_django_test.urls_overridden'

    def test_urls(self):
        resp = self.client.get('/overridden_url/')
        self.assertEqual(force_text(resp.content), 'Overridden urlconf works!')


def test_sole_test(django_testdir):
    """
    Make sure the database are configured when only Django TestCase classes
    are collected, without the django_db marker.
    """

    django_testdir.create_test_module('''
        from django.test import TestCase
        from django.conf import settings

        from .app.models import Item

        class TestFoo(TestCase):
            def test_foo(self):
                # Make sure we are actually using the test database
                db_name = settings.DATABASES['default']['NAME']
                assert db_name.startswith('test_') or db_name == ':memory:'

                # Make sure it is usable
                assert Item.objects.count() == 0
    ''')

    result = django_testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        "*TestFoo*test_foo PASSED*",
    ])
    assert result.ret == 0


class TestCaseWithDbFixture(TestCase):
    pytestmark = pytest.mark.usefixtures('db')

    def test_simple(self):
        # We only want to check setup/teardown does not conflict
        assert 1


class TestCaseWithTrDbFixture(TestCase):
    pytestmark = pytest.mark.usefixtures('transactional_db')

    def test_simple(self):
        # We only want to check setup/teardown does not conflict
        assert 1
