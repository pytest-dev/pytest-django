'''
Created on Jul 25, 2010

@author: ruben
'''

from pytest_django import plugin
from django.test.testcases import TransactionTestCase, TestCase

def test_get_testcase():
    django_testcase = TransactionTestCase(methodName='__init__')
    assert plugin._get_testcase(django_testcase) == django_testcase
    django_testcase = TestCase(methodName='__init__')
    assert plugin._get_testcase(django_testcase) == django_testcase
    assert isinstance(plugin._get_testcase(lambda x: x), TestCase)
    
def test_is_testcase():
    assert plugin._is_unittest(TransactionTestCase(methodName='__init__'))
    assert plugin._is_unittest(TestCase(methodName='__init__'))
    assert not plugin._is_unittest(None)
    