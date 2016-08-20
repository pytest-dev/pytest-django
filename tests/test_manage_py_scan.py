import pytest


@pytest.mark.django_project(project_root='django_project_root',
                            create_manage_py=True)
def test_django_project_found(django_testdir):
    # XXX: Important: Do not chdir() to django_project_root since runpytest_subprocess
    # will call "python /path/to/pytest.py", which will impliclity add cwd to
    # the path. By instead calling "python /path/to/pytest.py
    # django_project_root", we avoid impliclity adding the project to sys.path
    # This matches the behaviour when pytest is called directly as an
    # executable (cwd is not added to the Python path)

    django_testdir.create_test_module("""
    def test_foobar():
        assert 1 + 1 == 2
    """)

    result = django_testdir.runpytest_subprocess('django_project_root')
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
