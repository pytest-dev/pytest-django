import shutil

import py
import pytest

from django.test import TestCase
from app.models import Item


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
    urls = 'tests.urls_unittest'

    def test_urls(self):
        self.assertEqual(self.client.get('/test_url/').content,
                         'Test URL works!')


def test_sole_test(testdir):
    # Test TestCase when no pytest-django test ran before
    app = py.path.local(__file__).join('..', 'app')
    print app
    shutil.copytree(str(app), str(testdir.tmpdir.join('app')))
    testdir.makepyfile("""
        from django.test import TestCase
        from app.models import Item

        class TestFoo(TestCase):
            def test_foo(self):
                assert Item.objects.count() == 0
    """)
    r = testdir.runpytest()
    assert r.ret == 0


@pytest.mark.usefixtures('db')
class TestCaseWithDbFixture(TestCase):

    def test_simple(self):
        # We only want to check setup/teardown does not conflict
        assert 1


@pytest.mark.usefixtures('transactional_db')
class TestCaseWithTrDbFixture(TestCase):

    def test_simple(self):
        # We only want to check setup/teardown does not conflict
        assert 1
