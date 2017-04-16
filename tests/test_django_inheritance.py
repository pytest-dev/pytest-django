import pytest
from pytest_django.lazy_django import get_django_version


class TestDjangoInheritance:
    @pytest.mark.skipif(get_django_version() < (1, 7), reason=('Django < 1.8 doesn\'t have setUpTestData'))
    def test_django(self, django_testdir):
        django_testdir.create_test_module('''
            from django.test import TestCase

            class TestBase(TestCase):
                @classmethod
                def setUpClass(cls):
                    print('\\nCALLED: TestBase.setUpClass')
                    super(TestBase, cls).setUpClass()

                @classmethod
                def setUpTestData(cls):
                    print('\\nCALLED: TestBase.setUpTestData')
                    super(TestBase, cls).setUpTestData()

                @classmethod
                def tearDownClass(cls):
                    print('\\nCALLED: TestBase.tearDownClass')
                    super(TestBase, cls).tearDownClass()

                def test_pass(self):
                    print('\\nCALLED: TestBase.test_pass')

            class TestDerived(TestBase):
                @classmethod
                def setUpClass(cls):
                    print('\\nCALLED: TestDerived.setUpClass')
                    super(TestDerived, cls).setUpClass()

                @classmethod
                def setUpTestData(cls):
                    print('\\nCALLED: TestDerived.setUpTestData')
                    super(TestDerived, cls).setUpTestData()

                @classmethod
                def tearDownClass(cls):
                    print('\\nCALLED: TestDerived.tearDownClass')
                    super(TestDerived, cls).tearDownClass()

                def test_derived(self):
                    print('\\nCALLED: TestDerived.test_derived')
            ''')

        result = django_testdir.runpytest('-v', '-s')
        result.stdout.fnmatch_lines([
            # TestBase execution
            "CALLED: TestBase.setUpClass",
            "CALLED: TestBase.setUpTestData",
            "CALLED: TestBase.test_pass",
            "CALLED: TestBase.tearDownClass",

            # TestDerived execution
            "CALLED: TestDerived.setUpClass",
            "CALLED: TestBase.setUpClass",
            "CALLED: TestDerived.setUpTestData",    # TODO This line breaks!
            "CALLED: TestBase.setUpTestData",
            "CALLED: TestDerived.test_derived",
            "CALLED: TestBase.test_pass",

            "CALLED: TestBase.tearDownClass",   # TODO tear down in wrong order (?)
            "CALLED: TestDerived.tearDownClass",
        ])
        assert result.ret == 0
