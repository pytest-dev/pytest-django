# This file cannot be imported from until Django sets up
try:
    # Django 1.11+
    from django.test.utils import setup_databases, teardown_databases  # noqa: F401, F811
except ImportError:
    # In Django prior to 1.11, teardown_databases is only available as a method on DiscoverRunner
    from django.test.runner import setup_databases, DiscoverRunner  # noqa: F401, F811

    def teardown_databases(db_cfg, verbosity):
        DiscoverRunner(verbosity=verbosity, interactive=False).teardown_databases(
            db_cfg
        )
