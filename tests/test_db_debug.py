def test_debug_sql_setting(django_testdir):
    django_testdir.create_test_module(
        """
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_fail_with_db_queries():
            assert Item.objects.count() == 0
            assert 0, "triggered failure"
    """
    )
    django_testdir.makeini(
        """
       [pytest]
       django_debug_sql = 1
    """
    )

    result = django_testdir.runpytest_subprocess()
    assert result.ret == 1
    result.stdout.fnmatch_lines([
        "*- Captured log setup -*",
        "*CREATE TABLE*",
        "*- Captured log call -*",
        "*SELECT COUNT*",
    ])


def test_debug_sql_with_django_setup(django_testdir):
    django_testdir.create_test_module(
        """
        import pytest

        from .app.models import Item

        @pytest.mark.django_db
        def test_fail_with_db_queries():
            import django
            django.setup()

            assert Item.objects.count() == 0
            assert 0, "triggered failure"
    """
    )
    django_testdir.makeini(
        """
       [pytest]
       django_debug_sql = 1
    """
    )

    result = django_testdir.runpytest_subprocess()
    assert result.ret == 1
    result.stdout.fnmatch_lines([
        # "*- Captured stdout setup -*",
        "*- Captured log setup -*",
        "*CREATE TABLE*",
        "*= warnings summary =*",
        "*Debug logging level of django.db.backends was changed (to 0).*",
    ])
    assert "SELECT COUNT" not in result.stdout.str()
