import copy
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail, management
from django.core.management import call_command
from django.core.urlresolvers import clear_url_caches
from django.db import connection, transaction
from django.test.client import Client
from django.test.testcases import TestCase, disable_transaction_methods, restore_transaction_methods
from django.test.utils import setup_test_environment, teardown_test_environment
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.
from pytest_django.client import RequestFactory

class DjangoManager(object):
    """
    A Django plugin for py.test that handles creating and destroying the
    test environment and test database.
    
    Similar to Django's TransactionTestCase, a transaction is started and
    rolled back for each test. Additionally, the settings are copied before
    each test and restored at the end of the test, so it is safe to modify
    settings within tests.
    """
    
    def __init__(self, verbosity=0, noinput=False, copy_live_db=False, database=''):
        self.verbosity = verbosity
        self.noinput = noinput
        self.copy_live_db = copy_live_db
        self.database = database
        
        self._old_database_name = None
        self._old_settings = []
        self._old_urlconf = None
    
    def pytest_sessionstart(self, session):
        setup_test_environment()
        settings.DEBUG = False
        if self.database:
            settings.DATABASE_NAME = self.database
        
        management.get_commands()
        management._commands['syncdb'] = 'django.core'
        if 'south' in settings.INSTALLED_APPS and hasattr(settings, "SOUTH_TESTS_MIGRATE") and settings.SOUTH_TESTS_MIGRATE:
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
        
        self._old_database_name = settings.DATABASE_NAME
        create_test_db(self.verbosity, autoclobber=self.noinput, copy_test_db=self.copy_live_db)

    def pytest_sessionfinish(self, session, exitstatus):
        connection.creation.destroy_test_db(self._old_database_name, self.verbosity)
        teardown_test_environment()
    
    def pytest_itemstart(self, item):
        # This lets us control the order of the setup/teardown
        # Yuck.
        if self._is_unittest(self._get_item_obj(item)):
            item.setup = lambda: None
            item.teardown = lambda: None
    
    def pytest_runtest_setup(self, item):
        item_obj = self._get_item_obj(item)
        
        # Set the URLs if the py.test.urls() decorator has been applied
        if hasattr(item.obj, 'urls'):
            self._old_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = item.obj.urls
            clear_url_caches()
            
        # This is a Django unittest TestCase
        if self._is_unittest(item_obj):            
            # We have to run these here since py.test's unittest plugin skips
            # __call__()
            item_obj.client = Client()
            item_obj._pre_setup()
            item_obj.setUp()
            return
        
        if not settings.DATABASE_SUPPORTS_TRANSACTIONS:
            call_command('flush', verbosity=self.verbosity, interactive=not self.noinput)
        else:
            transaction.enter_transaction_management()
            transaction.managed(True)
            disable_transaction_methods()

            from django.contrib.sites.models import Site
            Site.objects.clear_cache()

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
        
        if hasattr(item, 'urls') and self._old_urlconf is not None:
            settings.ROOT_URLCONF = self._old_urlconf
            self._old_urlconf = None
        
    def _get_item_obj(self, item):
        try:
            return item.obj.im_self
        except AttributeError:
            return None
    
    def _is_unittest(self, item_obj):
        return issubclass(type(item_obj), TestCase)
    
    def pytest_namespace(self):
        """
        Sets up the py.test.params decorator.
        """
        def params(funcarglist):
            """
            A decorator to make parametrised tests easy. Takes a list of 
            dictionaries of keyword arguments for the function. A test is 
            created for each dictionary.

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
                'verbosity': self.verbosity + 1,
                'commit': not settings.DATABASE_SUPPORTS_TRANSACTIONS
            })
        
        def urls(urlconf):
            """
            A decorator to change the URLconf for a particular test, similar 
            to the `urls` attribute on Django's `TestCase`.
            
            Example:
            
                @py.test.urls('myapp.test_urls')
                def test_something(client):
                    assert 'Success!' in client.get('/some_path/')
            """
            def wrapper(function):
                function.urls = urlconf
            return wrapper
        
        return {'params': params, 'load_fixture': load_fixture, 'urls': urls}

    def pytest_generate_tests(self, metafunc):
        """
        Generates parametrised tests if the py.test.params decorator has been 
        used.
        """
        for funcargs in getattr(metafunc.function, 'funcarglist', ()):  
            metafunc.addcall(funcargs=funcargs)

    
def pytest_configure(config):
    verbosity = 0
    if config.getvalue('verbose'):
        verbosity = 1
    config.pluginmanager.register(DjangoManager(
                                    verbosity=verbosity, 
                                    noinput=config.getvalue('noinput'),
                                    copy_live_db=config.getvalue('copy_live_db'),
                                    database=config.getvalue('database_name')
                                 ))


######################################
# funcargs
######################################

def pytest_funcarg__client(request):
    """
    Returns a Django test client instance.
    """
    return Client()

def pytest_funcarg__admin_client(request):
    """
    Returns a Django test client logged in as an admin user.
    """
    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com', 
                                        'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
    client = Client()
    client.login(username='admin', password='password')
    
    return client    

def pytest_funcarg__rf(request):
    """
    Returns a RequestFactory instance.
    """
    return RequestFactory()

def pytest_funcarg__settings(request):
    """
    Returns a Django settings object that restores any changes after the test 
    has been run.
    """
    old_settings = copy.deepcopy(settings)
    def restore_settings():
        for setting in dir(old_settings):
            if setting == setting.upper():
                setattr(settings, setting, getattr(old_settings, setting))
    request.addfinalizer(restore_settings)
    return settings



def create_test_db(verbosity=1, autoclobber=False, copy_test_db=False):
    """
    Creates a test database, prompting the user for confirmation if the
    database already exists. Returns the name of the test database created.
    """
    if verbosity >= 1:
        print "Creating test database..."

    test_database_name = connection.creation._create_test_db(verbosity, autoclobber)

    connection.close()
    old_database_name = settings.DATABASE_NAME
    settings.DATABASE_NAME = test_database_name

    connection.settings_dict["DATABASE_NAME"] = test_database_name
    can_rollback = connection.creation._rollback_works()
    settings.DATABASE_SUPPORTS_TRANSACTIONS = can_rollback
    connection.settings_dict["DATABASE_SUPPORTS_TRANSACTIONS"] = can_rollback
    
    if copy_test_db:
        if verbosity >= 1:
            print "Copying database %s to test..." % copy_test_db
        try:
            # --copy_live_db is either 'data' or 'schema'. the choices are
            # controlled by the management command, so by the time we're here
            # we just assume that if it's "schema" we add -d, if not we don't
            no_data_opt='-d '
            if copy_test_db != 'schema':
                no_data_opt=''
            os.system("sh -c 'mysqldump -u %s %s %s | mysql -u %s %s'" %
                      (settings.DATABASE_USER, no_data_opt, old_database_name, settings.DATABASE_USER,test_database_name))
        except Exception, e:
            raise e

    call_command('syncdb', verbosity=verbosity, interactive=False)
    if 'south' in settings.INSTALLED_APPS and hasattr(settings, "SOUTH_TESTS_MIGRATE") and settings.SOUTH_TESTS_MIGRATE:
        call_command('migrate', '', verbosity=verbosity)

    if settings.CACHE_BACKEND.startswith('db://'):
        cache_name = settings.CACHE_BACKEND[len('db://'):]
        call_command('createcachetable', cache_name)

    # Get a cursor (even though we don't need one yet). This has
    # the side effect of initializing the test database.
    cursor = connection.cursor()

    return test_database_name
