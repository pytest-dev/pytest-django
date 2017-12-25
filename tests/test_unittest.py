import pytest
from django.test import TestCase

from pytest_django_test.app.models import Item


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


def test_sole_test(django_testdir):
    """
    Make sure the database are configured when only Django TestCase classes
    are collected, without the django_db marker.
    """

    django_testdir.create_test_module('''
        import os

        from django.test import TestCase
        from django.conf import settings

        from .app.models import Item

        class TestFoo(TestCase):
            def test_foo(self):
                # Make sure we are actually using the test database
                _, db_name = os.path.split(settings.DATABASES['default']['NAME'])
                assert db_name.startswith('test_') or db_name == ':memory:' \\
                    or 'file:memorydb' in db_name

                # Make sure it is usable
                assert Item.objects.count() == 0
    ''')

    result = django_testdir.runpytest_subprocess('-v')
    result.stdout.fnmatch_lines([
        "*TestFoo*test_foo PASSED*",
    ])
    assert result.ret == 0


class TestUnittestMethods:
    "Test that setup/teardown methods of unittests are being called."
    def test_django(self, django_testdir):
        django_testdir.create_test_module('''
            from django.test import TestCase

            class TestFoo(TestCase):
                @classmethod
                def setUpClass(self):
                    print('\\nCALLED: setUpClass')

                def setUp(self):
                    print('\\nCALLED: setUp')

                def tearDown(self):
                    print('\\nCALLED: tearDown')

                @classmethod
                def tearDownClass(self):
                    print('\\nCALLED: tearDownClass')

                def test_pass(self):
                    pass
        ''')

        result = django_testdir.runpytest_subprocess('-v', '-s')
        result.stdout.fnmatch_lines([
            "CALLED: setUpClass",
            "CALLED: setUp",
            "CALLED: tearDown",
            "PASSED*",
            "CALLED: tearDownClass",
        ])
        assert result.ret == 0

    def test_setUpClass_not_being_a_classmethod(self, django_testdir):
        django_testdir.create_test_module('''
            from django.test import TestCase

            class TestFoo(TestCase):
                def setUpClass(self):
                    pass

                def test_pass(self):
                    pass
        ''')

        result = django_testdir.runpytest_subprocess('-v', '-s')
        result.stdout.fnmatch_lines([
            "* ERROR at setup of TestFoo.test_pass *",
            "E *Failed: <class 'tpkg.test_the_test.TestFoo'>.setUpClass should be a classmethod",  # noqa:E501
        ])
        assert result.ret == 1

    def test_multi_inheritance_setUpClass(self, django_testdir):
        django_testdir.create_test_module('''
            from django.test import TestCase
            from .app.models import Item

            # Using a mixin is a regression test, see #280 for more details:
            # https://github.com/pytest-dev/pytest-django/issues/280

            class SomeMixin(object):
                pass

            class TestA(SomeMixin, TestCase):
                expected_state = ['A']
                state = []

                @classmethod
                def setUpClass(cls):
                    super(TestA, cls).setUpClass()
                    cls.state.append('A')

                @classmethod
                def tearDownClass(cls):
                    assert cls.state.pop() == 'A'
                    super(TestA, cls).tearDownClass()

                def test_a(self):
                    assert self.state == self.expected_state

            class TestB(TestA):
                expected_state = ['A', 'B']

                @classmethod
                def setUpClass(cls):
                    super(TestB, cls).setUpClass()
                    cls.state.append('B')

                @classmethod
                def tearDownClass(cls):
                    assert cls.state.pop() == 'B'
                    super(TestB, cls).tearDownClass()

                def test_b(self):
                    assert self.state == self.expected_state

            class TestC(TestB):
                expected_state = ['A', 'B', 'C']

                @classmethod
                def setUpClass(cls):
                    super(TestC, cls).setUpClass()
                    cls.state.append('C')

                @classmethod
                def tearDownClass(cls):
                    assert cls.state.pop() == 'C'
                    super(TestC, cls).tearDownClass()

                def test_c(self):
                    assert self.state == self.expected_state
        ''')

        result = django_testdir.runpytest_subprocess('-vvvv', '-s')
        assert result.parseoutcomes()['passed'] == 6
        assert result.ret == 0

    def test_unittest(self, django_testdir):
        django_testdir.create_test_module('''
            from unittest import TestCase

            class TestFoo(TestCase):
                @classmethod
                def setUpClass(self):
                    print('\\nCALLED: setUpClass')

                def setUp(self):
                    print('\\nCALLED: setUp')

                def tearDown(self):
                    print('\\nCALLED: tearDown')

                @classmethod
                def tearDownClass(self):
                    print('\\nCALLED: tearDownClass')

                def test_pass(self):
                    pass
        ''')

        result = django_testdir.runpytest_subprocess('-v', '-s')
        result.stdout.fnmatch_lines([
            "CALLED: setUpClass",
            "CALLED: setUp",
            "CALLED: tearDown",
            "PASSED*",
            "CALLED: tearDownClass",
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


def test_pdb_enabled(django_testdir):
    """
    Make sure the database is flushed and tests are isolated when
    using the --pdb option.

    See issue #405 for details:
    https://github.com/pytest-dev/pytest-django/issues/405
    """

    django_testdir.create_test_module('''
        import os

        from django.test import TestCase
        from django.conf import settings

        from .app.models import Item

        class TestPDBIsolation(TestCase):
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

    ''')

    result = django_testdir.runpytest_subprocess('-v', '--pdb')
    assert result.ret == 0
