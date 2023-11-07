import pytest
from django.test import SimpleTestCase, TestCase, tag

from .helpers import DjangoPytester

from pytest_django_test.app.models import Item


class TestFixtures(TestCase):
    fixtures = ("items",)

    def test_fixtures(self) -> None:
        assert Item.objects.count() == 1
        assert Item.objects.get().name == "Fixture item"

    def test_fixtures_again(self) -> None:
        """Ensure fixtures are only loaded once."""
        self.test_fixtures()


class TestSetup(TestCase):
    def setUp(self) -> None:
        """setUp should be called after starting a transaction"""
        assert Item.objects.count() == 0
        Item.objects.create(name="Some item")
        Item.objects.create(name="Some item again")

    def test_count(self) -> None:
        self.assertEqual(Item.objects.count(), 2)  # noqa: PT009
        assert Item.objects.count() == 2
        Item.objects.create(name="Foo")
        self.assertEqual(Item.objects.count(), 3)  # noqa: PT009

    def test_count_again(self) -> None:
        self.test_count()

    def tearDown(self) -> None:
        """tearDown should be called before rolling back the database"""
        assert Item.objects.count() == 3


class TestFixturesWithSetup(TestCase):
    fixtures = ("items",)

    def setUp(self) -> None:
        assert Item.objects.count() == 1
        Item.objects.create(name="Some item")

    def test_count(self) -> None:
        assert Item.objects.count() == 2
        Item.objects.create(name="Some item again")

    def test_count_again(self) -> None:
        self.test_count()

    def tearDown(self) -> None:
        assert Item.objects.count() == 3


@tag("tag1", "tag2")
class TestDjangoTagsToPytestMarkers(SimpleTestCase):
    """Django test tags are converted to Pytest markers, at the class & method
    levels."""

    @pytest.fixture(autouse=True)
    def gimme_my_markers(self, request: pytest.FixtureRequest) -> None:
        self.markers = {m.name for m in request.node.iter_markers()}

    @tag("tag3", "tag4")  # type: ignore[misc]
    def test_1(self) -> None:
        assert self.markers == {"tag1", "tag2", "tag3", "tag4"}

    def test_2(self) -> None:
        assert self.markers == {"tag1", "tag2"}

    @tag("tag5")  # type: ignore[misc]
    def test_3(self) -> None:
        assert self.markers == {"tag1", "tag2", "tag5"}


@tag("tag1")
class TestNonDjangoClassWithTags:
    """Django test tags are only converted to Pytest markers if actually
    Django tests. Use pytest markers directly for pytest tests."""

    @pytest.fixture(autouse=True)
    def gimme_my_markers(self, request: pytest.FixtureRequest) -> None:
        self.markers = {m.name for m in request.node.iter_markers()}

    @tag("tag2")  # type: ignore[misc]
    def test_1(self) -> None:
        assert not self.markers


def test_sole_test(django_pytester: DjangoPytester) -> None:
    """
    Make sure the database is configured when only Django TestCase classes
    are collected, without the django_db marker.

    Also ensures that the DB is available after a failure (#824).
    """
    django_pytester.create_test_module(
        """
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

                assert 0, "trigger_error"

        class TestBar(TestCase):
            def test_bar(self):
                assert Item.objects.count() == 0
    """
    )

    result = django_pytester.runpytest_subprocess("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_foo FAILED",
            "*::test_bar PASSED",
            '>       assert 0, "trigger_error"',
            "E       AssertionError: trigger_error",
            "E       assert 0",
            "*= 1 failed, 1 passed*",
        ]
    )
    assert result.ret == 1


class TestUnittestMethods:
    "Test that setup/teardown methods of unittests are being called."

    def test_django(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
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
        """
        )

        result = django_pytester.runpytest_subprocess("-v", "-s")
        result.stdout.fnmatch_lines(
            [
                "CALLED: setUpClass",
                "CALLED: setUp",
                "CALLED: tearDown",
                "PASSED*",
                "CALLED: tearDownClass",
            ]
        )
        assert result.ret == 0

    def test_setUpClass_not_being_a_classmethod(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import TestCase

            class TestFoo(TestCase):
                def setUpClass(self):
                    pass

                def test_pass(self):
                    pass
        """
        )

        result = django_pytester.runpytest_subprocess("-v", "-s")
        expected_lines = [
            "* ERROR at setup of TestFoo.test_pass *",
            "E * TypeError: *",
        ]
        result.stdout.fnmatch_lines(expected_lines)
        assert result.ret == 1

    def test_setUpClass_multiple_subclasses(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import TestCase


            class TestFoo(TestCase):
                @classmethod
                def setUpClass(cls):
                    super(TestFoo, cls).setUpClass()

                def test_shared(self):
                    pass


            class TestBar(TestFoo):
                def test_bar1(self):
                    pass


            class TestBar2(TestFoo):
                def test_bar21(self):
                    pass
        """
        )

        result = django_pytester.runpytest_subprocess("-v")
        result.stdout.fnmatch_lines(
            [
                "*TestFoo::test_shared PASSED*",
                "*TestBar::test_bar1 PASSED*",
                "*TestBar::test_shared PASSED*",
                "*TestBar2::test_bar21 PASSED*",
                "*TestBar2::test_shared PASSED*",
            ]
        )
        assert result.ret == 0

    def test_setUpClass_mixin(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import TestCase

            class TheMixin:
                @classmethod
                def setUpClass(cls):
                    super(TheMixin, cls).setUpClass()


            class TestFoo(TheMixin, TestCase):
                def test_foo(self):
                    pass


            class TestBar(TheMixin, TestCase):
                def test_bar(self):
                    pass
        """
        )

        result = django_pytester.runpytest_subprocess("-v")
        result.stdout.fnmatch_lines(["*TestFoo::test_foo PASSED*", "*TestBar::test_bar PASSED*"])
        assert result.ret == 0

    def test_setUpClass_skip(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import TestCase
            import pytest


            class TestFoo(TestCase):
                @classmethod
                def setUpClass(cls):
                    if cls is TestFoo:
                        raise pytest.skip("Skip base class")
                    super(TestFoo, cls).setUpClass()

                def test_shared(self):
                    pass


            class TestBar(TestFoo):
                def test_bar1(self):
                    pass


            class TestBar2(TestFoo):
                def test_bar21(self):
                    pass
        """
        )

        result = django_pytester.runpytest_subprocess("-v")
        result.stdout.fnmatch_lines(
            [
                "*TestFoo::test_shared SKIPPED*",
                "*TestBar::test_bar1 PASSED*",
                "*TestBar::test_shared PASSED*",
                "*TestBar2::test_bar21 PASSED*",
                "*TestBar2::test_shared PASSED*",
            ]
        )
        assert result.ret == 0

    def test_multi_inheritance_setUpClass(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import TestCase

            # Using a mixin is a regression test, see #280 for more details:
            # https://github.com/pytest-dev/pytest-django/issues/280

            class SomeMixin:
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
        """
        )

        result = django_pytester.runpytest_subprocess("-vvvv", "-s")
        assert result.parseoutcomes()["passed"] == 6
        assert result.ret == 0

    def test_unittest(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
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
        """
        )

        result = django_pytester.runpytest_subprocess("-v", "-s")
        result.stdout.fnmatch_lines(
            [
                "CALLED: setUpClass",
                "CALLED: setUp",
                "CALLED: tearDown",
                "PASSED*",
                "CALLED: tearDownClass",
            ]
        )
        assert result.ret == 0

    def test_setUpClass_leaf_but_not_in_dunder_dict(self, django_pytester: DjangoPytester) -> None:
        django_pytester.create_test_module(
            """
            from django.test import testcases

            class CMSTestCase(testcases.TestCase):
                pass

            class FooBarTestCase(testcases.TestCase):

                @classmethod
                def setUpClass(cls):
                    print('FooBarTestCase.setUpClass')
                    super(FooBarTestCase, cls).setUpClass()

            class TestContact(CMSTestCase, FooBarTestCase):

                def test_noop(self):
                    print('test_noop')
        """
        )

        result = django_pytester.runpytest_subprocess("-q", "-s")
        result.stdout.fnmatch_lines(["*FooBarTestCase.setUpClass*", "*test_noop*", "1 passed*"])
        assert result.ret == 0


class TestCaseWithDbFixture(TestCase):
    pytestmark = pytest.mark.usefixtures("db")

    def test_simple(self) -> None:
        # We only want to check setup/teardown does not conflict
        assert 1


class TestCaseWithTrDbFixture(TestCase):
    pytestmark = pytest.mark.usefixtures("transactional_db")

    def test_simple(self) -> None:
        # We only want to check setup/teardown does not conflict
        assert 1


def test_pdb_enabled(django_pytester: DjangoPytester) -> None:
    """
    Make sure the database is flushed and tests are isolated when
    using the --pdb option.

    See issue #405 for details:
    https://github.com/pytest-dev/pytest-django/issues/405
    """

    django_pytester.create_test_module(
        '''
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

    '''
    )

    result = django_pytester.runpytest_subprocess("-v", "--pdb")
    assert result.ret == 0


def test_debug_not_used(django_pytester: DjangoPytester) -> None:
    django_pytester.create_test_module(
        """
        from django.test import TestCase

        pre_setup_count = 0


        class TestClass1(TestCase):

            def debug(self):
                assert 0, "should not be called"

            def test_method(self):
                pass
    """
    )

    result = django_pytester.runpytest_subprocess("--pdb")
    result.stdout.fnmatch_lines(["*= 1 passed*"])
    assert result.ret == 0
