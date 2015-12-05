#!/usr/bin/env python
from __future__ import print_function

import itertools
from collections import namedtuple
from textwrap import dedent

# https://xkcd.com/1319/
# https://xkcd.com/1205/


TestEnvBase = namedtuple('TestEnvBase', ['python_version', 'pytest_version',
                                         'django_version', 'settings'])

class TestEnv(TestEnvBase):
    def is_py2(self):
        return self.python_version.startswith('python2') or self.python_version == 'pypy'

    def is_py3(self):
        return self.python_version.startswith('python3') or self.python_version == 'pypy3'

    def is_pypy(self):
        return self.python_version.startswith('pypy')

# Python to run tox.
RUN_PYTHON = '3.5'
PYTHON_MAIN_VERSIONS = ['python2.7', 'python3.4']
PYTHON_VERSIONS = ['python2.6', 'python2.7', 'python3.2', 'python3.3',
                   'python3.4', 'python3.5', 'pypy', 'pypy3']
PYTEST_VERSIONS = ['2.7.3', '2.8.1']
DJANGO_VERSIONS = ['1.4', '1.5', '1.6', '1.7', '1.8', '1.9', 'master']
SETTINGS = ['sqlite', 'sqlite_file', 'mysql_myisam', 'mysql_innodb',
            'postgres']
DJANGO_REQUIREMENTS = {
    '1.4': 'Django>=1.4,<1.5',
    '1.5': 'Django>=1.5,<1.6',
    '1.6': 'Django>=1.6,<1.7',
    '1.7': 'Django>=1.7,<1.8',
    '1.8': 'Django>=1.8,<1.9',
    '1.9': 'Django==1.9a1',
    'master': 'https://github.com/django/django/archive/master.tar.gz',
}

TOX_TESTENV_TEMPLATE = dedent("""
    [testenv:%(testenv_name)s]
    commands =
    %(commands)s
    basepython = %(python_version)s
    deps =
    %(deps)s
    setenv =
         PYTHONPATH = {toxinidir}:{env:PYTHONPATH:}
         UID = %(uid)s
    """)


def is_valid_env(env):

    # Stable database adapters for PyPy+Postgres/MySQL are hard to come by..
    if env.is_pypy() and env.settings in ('postgres', 'mysql_myisam', 'mysql_innodb'):
        return False

    if env.is_py3():
        # Django <1.5 does not support Python 3
        if env.django_version == '1.4':
            return False

        # MySQL on Python 3 is not supported by Django
        if env.settings in ('mysql_myisam', 'mysql_innodb'):
            return False

    # Django 1.7 dropped Python 2.6 support
    if env.python_version == 'python2.6' and env.django_version in ('1.7', '1.8', '1.9', 'master'):
        return False

    # Django 1.9 dropped Python 3.2 and Python 3.3 support
    if (env.python_version in ('python3.2', 'python3.3') and
        env.django_version in ('1.7', '1.8', '1.9', 'master')):
        return False

    # Python 3.5 is only supported by Django 1.8+
    if env.python_version == 'python3.5':
        return env.django_version in ('1.8', '1.9', 'master')

    # pypy3 is compatible with Python 3.2, but Django 1.9 only supports Python 2.7, 3.4+.
    if env.python_version == 'pypy3' and env.django_version in ('1.9', 'master'):
        return False

    return True


def requirements(env):
    yield 'pytest==%s' % (env.pytest_version)
    yield 'pytest-xdist==1.13.1'
    yield DJANGO_REQUIREMENTS[env.django_version]
    yield 'django-configurations==0.8'

    if env.is_py2():
        yield 'south==1.0.2'

    if env.settings == 'postgres':
        yield 'psycopg2==2.6.1'

    if env.settings in ('mysql_myisam', 'mysql_innodb'):
        yield 'mysql-python==1.2.5'


def commands(uid, env):
    # Django versions prior to 1.7 must have the production database available
    # https://code.djangoproject.com/ticket/16969
    db_name = 'pytest_django_%s' % uid

    # The sh trickery always exits with 0
    if env.settings in ('mysql_myisam', 'mysql_innodb'):
        yield 'sh -c "mysql -u root -e \'drop database if exists %(name)s;' \
            ' create database %(name)s\'" || exit 0' % {'name': db_name}

    if env.settings == 'postgres':
        yield 'sh -c "dropdb %(name)s;' \
            ' createdb %(name)s || exit 0"' % {'name': db_name}

    yield 'py.test --ds=pytest_django_test.settings_%s --strict -r fEsxXw {posargs:tests}' % env.settings


def testenv_name(env):
    if len(PYTEST_VERSIONS) == 1:
        env = [getattr(env, x) for x in env._fields if x != 'pytest_version']
    return '-'.join(env)


def tox_testenv_config(uid, env):
    cmds = '\n'.join('    %s' % r for r in commands(uid, env))

    deps = '\n'.join('    %s' % r for r in requirements(env))

    return TOX_TESTENV_TEMPLATE % {
        'testenv_name': testenv_name(env),
        'python_version': env.python_version,
        'django_version': env.django_version,
        'settings': env.settings,
        'commands': cmds,
        'deps': deps,
        'uid': uid,
    }


def generate_all_envs():
    products = itertools.product(PYTHON_VERSIONS, PYTEST_VERSIONS,
                                 DJANGO_VERSIONS, SETTINGS)

    for (python_version, pytest_version, django_version, settings) \
            in products:
        env = TestEnv(python_version, pytest_version, django_version, settings)

        if is_valid_env(env):
            yield env


def generate_default_envs(envs):
    """
    Returns a list of testenvs that include all different Python versions, all
    Django versions and all database backends.
    """
    result = set()

    def find_and_add(variations, env_getter):
        for variation in variations:
            for existing in result:
                if env_getter(existing) == variation:
                    break
            else:
                for env in reversed(envs):
                    if env_getter(env) == variation:
                        result.add(env)
                        break

    # Add all Django versions for each main python version (2.x and 3.x).
    find_and_add(itertools.product(PYTHON_MAIN_VERSIONS, DJANGO_VERSIONS),
                 lambda env: (env.python_version, env.django_version))

    find_and_add(PYTHON_VERSIONS, lambda env: env.python_version)
    find_and_add(PYTEST_VERSIONS, lambda env: env.pytest_version)
    find_and_add(DJANGO_VERSIONS, lambda env: env.django_version)
    find_and_add(SETTINGS, lambda env: env.settings)

    return result


def make_tox_ini(envs, default_envs):
    default_env_names = ([testenv_name(env) for env in default_envs] +
                         ['checkqa-%s' % python_version for python_version in
                          PYTHON_MAIN_VERSIONS])

    contents = [dedent('''
        [tox]
        envlist = %(active_envs)s

        [testenv]
        whitelist_externals =
            sh
            ''' % {'active_envs': ','.join(default_env_names)}).lstrip()]

    # Add checkqa-testenvs for different PYTHON_VERSIONS.
    # flake8 is configured in setup.cfg.
    idx = 0
    for python_version in PYTHON_VERSIONS:
        idx = idx + 1
        contents.append(dedent("""
            [testenv:checkqa-%(python_version)s]
            commands =
                flake8 --version
                flake8 --show-source --statistics pytest_django tests
            basepython = %(python_version)s
            deps =
                flake8
            setenv =
                UID = %(uid)s""" % {
            'python_version': python_version,
            'uid': idx,
        }))

    for env in envs:
        idx = idx + 1
        contents.append(tox_testenv_config(idx, env))

    return '\n'.join(contents)


def make_travis_yml(envs):
    contents = dedent("""
        # Use container-based environment (faster startup, allows caches).
        sudo: false
        language: python
        python:
          - "%(RUN_PYTHON)s"
        env:
        %(testenvs)s
        %(checkenvs)s
        matrix:
          allow_failures:
        %(allow_failures)s
        install:
          # Create pip wrapper script, using travis_retry (a function) and
          # inject it into tox.ini.
          - mkdir -p bin
          - PATH=$PWD/bin:$PATH
          - printf '#!/bin/sh\\n' > bin/travis_retry_pip
          - declare -f travis_retry >> bin/travis_retry_pip
          - printf '\\necho "Using pip-wrapper.." >&2\\ntravis_retry pip "$@"' >> bin/travis_retry_pip
          - chmod +x bin/travis_retry_pip
          - sed -i.bak 's/^\[testenv\]/\\0\\ninstall_command = travis_retry_pip install {opts} {packages}/' tox.ini
          - diff tox.ini tox.ini.bak && return 1 || true
          - sed -i.bak 's/whitelist_externals =/\\0\\n    travis_retry_pip/' tox.ini
          - diff tox.ini tox.ini.bak && return 1 || true

          - pip install tox
        script: tox -e $TESTENV
        """).strip("\n")
    testenvs = '\n'.join('  - TESTENV=%s' % testenv_name(env) for env in envs)
    checkenvs = '\n'.join('  - TESTENV=checkqa-%s' %
                          python for python in PYTHON_MAIN_VERSIONS)
    allow_failures = '\n'.join('    - env: TESTENV=%s' %
                               testenv_name(env) for env in envs
                               if env.django_version == 'master')

    return contents % {
        'testenvs': testenvs,
        'checkenvs': checkenvs,
        'allow_failures': allow_failures,
        'RUN_PYTHON': RUN_PYTHON,
    }


def main():
    all_envs = sorted(generate_all_envs())
    default_envs = sorted(generate_default_envs(all_envs))

    with open('tox.ini', 'w+') as tox_ini_file:
        tox_ini_file.write(make_tox_ini(all_envs, default_envs))

    with open('.travis.yml', 'w+') as travis_yml_file:
        travis_yml_file.write(make_travis_yml(default_envs))

    print ('tox.ini and .travis.yml has been generated!')

if __name__ == '__main__':
    main()
