# This file cannot be imported from until Django sets up
try:
    # Django 1.11
    from django.test.utils import setup_databases, teardown_databases  # noqa: F401
except ImportError:
    # In Django prior to 1.11, teardown_databases is only available as a method on DiscoverRunner
    from django.test.runner import (  # noqa: F401
        setup_databases,
        DiscoverRunner as _DiscoverRunner,
    )

    def teardown_databases(db_cfg, verbosity):
        _DiscoverRunner(verbosity=verbosity, interactive=False).teardown_databases(
            db_cfg
        )


# Import NullTimeKeeper from Django > 3.1 for setup_databases call -
# fix for https://github.com/pytest-dev/pytest-django/issues/858
try:
    from django.test.utils import NullTimeKeeper
    setup_databases_args = {"time_keeper": NullTimeKeeper()}
except ImportError:
    setup_databases_args = {}
