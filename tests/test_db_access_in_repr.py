def test_db_access_with_repr_in_report(django_testdir):
    django_testdir.create_test_module(
        """
        import pytest

        from .app.models import Item

        def test_via_db_blocker(django_db_setup, django_db_blocker):
            with django_db_blocker.unblock():
                Item.objects.get(name='This one is not there')

        def test_via_db_fixture(db):
            Item.objects.get(name='This one is not there')
    """
    )

    result = django_testdir.runpytest_subprocess("--tb=auto")
    result.stdout.fnmatch_lines([
        "tpkg/test_the_test.py FF",
        "E   *DoesNotExist: Item matching query does not exist.",
        "tpkg/test_the_test.py:8: ",
        'self = *RuntimeError*Database access not allowed*',
        "E   *DoesNotExist: Item matching query does not exist.",
        "* 2 failed in *",
    ])
    assert "INTERNALERROR" not in str(result.stdout) + str(result.stderr)
    assert result.ret == 1
