from django.conf import settings
from django.core import mail, management
from django.core.management import call_command
from django.core.urlresolvers import clear_url_caches
from django.db import connection, transaction
from django.test.client import Client
from django.test.testcases import TestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from pytest_django.client import RequestFactory

real_commit = transaction.commit
real_rollback = transaction.rollback
real_enter_transaction_management = transaction.enter_transaction_management
real_leave_transaction_management = transaction.leave_transaction_management
real_managed = transaction.managed

def nop(*args, **kwargs):
    return

def disable_transaction_methods():
    transaction.commit = nop
    transaction.rollback = nop
    transaction.enter_transaction_management = nop
    transaction.leave_transaction_management = nop
    transaction.managed = nop

def restore_transaction_methods():
    transaction.commit = real_commit
    transaction.rollback = real_rollback
    transaction.enter_transaction_management = real_enter_transaction_management
    transaction.leave_transaction_management = real_leave_transaction_management
    transaction.managed = real_managed

class DjangoManager(object):
    """
    A Django plugin for py.test that handles creating and destroying the
    test environment and test database.
    
    Similar to Django's TransactionTestCase, a transaction is started and
    rolled back for each test. Additionally, the settings are copied before
    each test and restored at the end of the test, so it is safe to modify
    settings within tests.
    """
    
    old_database_name = None
    _old_settings = []
    
    def __init__(self, verbosity=0):
        self.verbosity = verbosity
    
    def pytest_sessionstart(self, session):
        setup_test_environment()
        settings.DEBUG = False
        
        management.get_commands()
        management._commands['syncdb'] = 'django.core'
        if hasattr(settings, "SOUTH_TESTS_MIGRATE") and settings.SOUTH_TESTS_MIGRATE:
            try:
                from south.management.commands.syncdb import Command
            except ImportError:
                pass
            else:
                class MigrateAndSyncCommand(Command):
                    option_list = Command.option_list
                    for opt in option_list:
                        if "--migrate" == opt.get_opt_string():
                            opt.default = True
                            break
                management._commands['syncdb'] = MigrateAndSyncCommand()
        
        self.old_database_name = settings.DATABASE_NAME
        connection.creation.create_test_db(self.verbosity)

    def pytest_sessionfinish(self, session, exitstatus):
        connection.creation.destroy_test_db(self.old_database_name, self.verbosity)
        teardown_test_environment()
    
    def pytest_itemstart(self, item):
        # This lets us control the order of the setup/teardown
        # Yuck.
        if self._is_unittest(self._get_item_obj(item)):
            item.setup = lambda: None
            item.teardown = lambda: None
    
    def pytest_runtest_setup(self, item):
        self._old_settings = settings
        item_obj = self._get_item_obj(item)
        
        # This is a Django unittest TestCase
        if self._is_unittest(item_obj):
            item_obj.client = Client()
            item_obj._pre_setup()
            item_obj.setUp()
            return
        
        if not settings.DATABASE_SUPPORTS_TRANSACTIONS:
            call_command('flush', verbosity=self.verbosity, interactive=False)
            if hasattr(item_obj, 'fixtures'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                call_command('loaddata', *item_obj.fixtures, **{
                    'verbosity': self.verbosity
                })
        else:
            transaction.enter_transaction_management()
            transaction.managed(True)
            disable_transaction_methods()

            from django.contrib.sites.models import Site
            Site.objects.clear_cache()

            if hasattr(item_obj, 'fixtures'):
                call_command('loaddata', *item_obj.fixtures, **{
                    'verbosity': self.verbosity,
                    'commit': False
                })
        if hasattr(item_obj, 'urls'):
            settings.ROOT_URLCONF = item_obj.urls
            clear_url_caches()

        mail.outbox = []
        
    def pytest_runtest_teardown(self, item):
        item_obj = self._get_item_obj(item)
        
        # This is a Django unittest TestCase
        if self._is_unittest(item_obj):
            item_obj.tearDown()
            item_obj._post_teardown()
            return
                    
        elif settings.DATABASE_SUPPORTS_TRANSACTIONS:
            restore_transaction_methods()
            transaction.rollback()
            try:
                transaction.leave_transaction_management()
            except transaction.TransactionManagementError:
                pass
            connection.close()
        
        for setting in dir(self._old_settings):
            if setting == setting.upper():
                setattr(self, setting, getattr(self._old_settings, setting))
    
    def _get_item_obj(self, item):
        try:
            return item.obj.im_self
        except AttributeError:
            return None
    
    def _is_unittest(self, item_obj):
        return issubclass(type(item_obj), TestCase)
        
def pytest_configure(config):
    verbosity = 0
    if config.getvalue('verbose'):
        verbosity = 1
    config.pluginmanager.register(DjangoManager(verbosity))

def pytest_funcarg__client(request):
    return Client()

def pytest_funcarg__rf(request):
    return RequestFactory()

def pytest_namespace():
    """
    Sets up the py.test.params decorator.
    """
    def params(funcarglist):
        """
        A decorator to make parametrised tests easy. Takes a list of 
        dictionaries of keyword arguments for the function. A test is created
        for each dictionary.
        
        Example:
        
            @py.test.params([dict(a=1, b=2), dict(a=3, b=3), dict(a=5, b=4)])  
            def test_equals(a, b):
                assert a == b
        """
        def wrapper(function):  
            function.funcarglist = funcarglist  
            return function  
        return wrapper
    
    def load_fixture(fixture):
        """
        Loads a fixture, useful for loading fixtures in funcargs.
        
        Example:
        
            def pytest_funcarg__articles(request):
                py.test.load_fixture('test_articles')
                return Article.objects.all()
        """
        call_command('loaddata', fixture, **{
            'verbosity': 0,
            'commit': not settings.DATABASE_SUPPORTS_TRANSACTIONS
        })
    
    return {'params': params, 'load_fixture': load_fixture}

def pytest_generate_tests(metafunc):
    """
    Generates parametrised tests if the py.test.params decorator has been 
    used.
    """
    for funcargs in getattr(metafunc.function, 'funcarglist', ()):  
        metafunc.addcall(funcargs=funcargs)  
