import pytest


@pytest.mark.django_project(project_root='django_project_root',
                            create_manage_py=True)
def test_django_project_found(django_testdir, monkeypatch):
    # NOTE: Important: the chdir() to django_project_root causes
    # runpytest_subprocess to call "python /path/to/pytest.py", which will
    # impliclity add cwd to the path.
    django_testdir.create_test_module("""
    def test_foobar():
        import os, sys

        cwd = os.getcwd()

        # The one inserted by Python, see comment above.
        assert sys.path[0] == cwd

        # The one inserted by us.  It should be absolute.
        # py37 has it in sys.path[1] already, but otherwise there is an empty
        # entry first.
        if sys.path[1] == '':
            assert sys.path[2] == cwd
        else:
            assert sys.path[1] == cwd
    """)
    monkeypatch.chdir('django_project_root')
    result = django_testdir.runpytest_subprocess('.')
    assert result.ret == 0

    outcomes = result.parseoutcomes()
    assert outcomes['passed'] == 1


@pytest.mark.django_project(project_root='django_project_root',
                            create_manage_py=True)
def test_django_project_found_invalid_settings(django_testdir, monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')

    result = django_testdir.runpytest_subprocess('django_project_root')
    assert result.ret != 0

    result.stderr.fnmatch_lines(['*ImportError:*DOES_NOT_EXIST*'])
    result.stderr.fnmatch_lines(['*pytest-django found a Django project*'])


def test_django_project_scan_disabled_invalid_settings(django_testdir,
                                                       monkeypatch):
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')

    django_testdir.makeini('''
    [pytest]
    django_find_project = false
    ''')

    result = django_testdir.runpytest_subprocess('django_project_root')
    assert result.ret != 0

    result.stderr.fnmatch_lines(['*ImportError*DOES_NOT_EXIST*'])
    result.stderr.fnmatch_lines(['*pytest-django did not search for '
                                 'Django projects*'])


@pytest.mark.django_project(project_root='django_project_root',
                            create_manage_py=True)
def test_django_project_found_invalid_settings_version(django_testdir, monkeypatch):
    """Invalid DSM should not cause an error with --help or --version."""
    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'DOES_NOT_EXIST')

    result = django_testdir.runpytest_subprocess('django_project_root', '--version')
    assert result.ret == 0
    result.stderr.fnmatch_lines(['*This is pytest version*'])

    result = django_testdir.runpytest_subprocess('django_project_root', '--help')
    assert result.ret == 0
    result.stdout.fnmatch_lines(['*usage:*'])
