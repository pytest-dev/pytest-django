import os
from optparse import make_option

import pytest


class PyTestRunner(object):
    """
    Runs py.test to discover and run tests.
    """
    option_list = (
        make_option('-t', '--top-level-directory',
                    action='store', dest='top_level', default=None,
                    help='Top level of project for unittest discovery.'),
        make_option('-p', '--pattern', action='store', dest='pattern',
                    default="test*.py",
                    help='The test matching pattern. Defaults to test*.py.'),
        make_option('-k', '--keepdb',
                    action='store_true', dest='keepdb', default=False,
                    help='Preserves the test DB between runs.'),
    )

    def __init__(self, pattern=None, top_level=None, verbosity=1,
                 interactive=True, failfast=False, keepdb=False, **kwargs):
        if pattern and pattern != 'test*.py':
            # TODO: implement
            raise NotImplementedError('Testing with a file pattern is not '
                                      'implemented.')
        if top_level is not None:
            # TODO: implement
            raise NotImplementedError('Specifying the top_level is not '
                                      'implemented.')
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.keepdb = keepdb

        # TODO: Make this an option
        self.ds = os.environ['DJANGO_SETTINGS_MODULE']

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """
        Run py.test and returns the exitcode.
        """
        if test_labels:
            # TODO: implement
            raise NotImplementedError('test_labels is not implemented.')
        if extra_tests is not None:
            # TODO: implement
            raise NotImplementedError('extra_tests is not implemented.')

        # Translate arguments
        argv = ['--ds', self.ds]
        if self.verbosity == 0:
            argv.append('--quiet')
        if self.verbosity == 2:
            argv.append('--verbose')
        if self.failfast:
            argv.append('--exitfirst')
        if self.keepdb:
            argv.append('--nomigrations')

        # Run py.test
        return pytest.main(argv)
