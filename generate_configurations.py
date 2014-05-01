from __future__ import print_function

# https://xkcd.com/1319/
# https://xkcd.com/1205/

import itertools
from collections import namedtuple

TestEnv = namedtuple('TestEnv', ['python_version', 'django_version', 'settings'])


PYTHON_VERSIONS = ['python2.6', 'python2.7', 'python3.2', 'python3.3', 'python3.4', 'pypy']
DJANGO_VERSIONS = ['1.3', '1.4', '1.5', '1.6', '1.7', 'master']
SETTINGS = ['sqlite', 'mysql_myisam', 'mysql_innodb', 'postgres']
DJANGO_REQUIREMENTS = {
    '1.3': 'Django==1.3.7',
    '1.4': 'Django==1.4.11',
    '1.5': 'Django==1.5.6',
    '1.6': 'Django==1.6.3',
    '1.7': 'https://www.djangoproject.com/m/releases/1.7/Django-1.7b2.tar.gz',
    'master': 'https://github.com/django/django/archive/master.zip',
}

TESTENV_TEMPLATE = """
[testenv:%(testenv_name)s]
commands =
%(commands)s
basepython = %(python_version)s
deps =
%(deps)s
setenv =
     DJANGO_SETTINGS_MODULE = tests.settings_%(settings)s
     PYTHONPATH = {toxinidir}
     UID = %(uid)s
"""


def is_valid_env(env):
    # Stable database adapters for PyPy+Postgres/MySQL are hard to come by..
    if env.python_version == 'pypy' and env.settings in ('postgres',
                                                         'mysql_myisam',
                                                         'mysql_innodb'):
        return False

    if env.python_version == 'pypy' and env.settings in 'mysql':
        return False

    if env.python_version in ('python3.2', 'python3.3', 'python3.4'):
        if env.django_version in ('1.3', '1.4'):
            return False

        # MySQL on Python 3 is not supported by Django
        if env.settings in ('mysql_myisam', 'mysql_innodb'):
            return False

    # Django 1.7 dropped Python 2.6 support
    if env.python_version == 'python2.6' and env.django_version in ('1.7', 'master'):
        return False

    return True


def requirements(env):
    yield 'pytest==2.5.2'
    yield 'pytest-xdist==1.10'
    yield DJANGO_REQUIREMENTS[env.django_version]
    yield 'django-configurations==0.8'

    if env.settings == 'postgres':
        # Django 1.3 does not work with recent psycopg2 versions
        if env.django_version == '1.3':
            yield 'psycopg2==2.4.1'
        else:
            yield 'psycopg2==2.5.2'

    if env.settings in ('mysql_myisam', 'mysql_innodb'):
        yield 'mysql-python==1.2.5'


def commands(uid, env):
    # Django versions prior to 1.7 must have the production database available
    # https://code.djangoproject.com/ticket/16969
    db_name = 'pytest_django_%s' % uid

    # The sh trickery always exits with 0
    if env.settings in ('mysql_myisam', 'mysql_innodb'):
        yield 'sh -c "mysql -u root -e \'drop database if exists %(name)s; create database %(name)s\'" || exit 0' % {'name': db_name}

    if env.settings == 'postgres':
        yield 'sh -c "dropdb %(name)s; createdb %(name)s || exit 0"' % {'name': db_name}

    yield 'py.test {posargs}'


def testenv_name(env):
    return '-'.join(env)


def testenv_config(uid, env):
    cmds = '\n'.join('    %s' % r for r in commands(uid, env))

    deps = '\n'.join('    %s' % r for r in requirements(env))

    return TESTENV_TEMPLATE % {
        'testenv_name': testenv_name(env),
        'python_version': env.python_version,
        'django_version': env.django_version,
        'settings': env.settings,
        'commands': cmds,
        'deps': deps,
        'uid': uid,
    }


def generate_all_envs():
    products = itertools.product(PYTHON_VERSIONS, DJANGO_VERSIONS, SETTINGS)

    for idx, (python_version, django_version, settings) in enumerate(products):
        env = TestEnv(python_version, django_version, settings)

        if is_valid_env(env):
            yield env


def generate_unique_envs(envs):
    """
    Returns a list of testenvs that include all different Python versions, all
    Django versions and all database backends.
    """
    result = set()

    def find_and_add(variations, env_getter):
        for variation in variations:
            for env in reversed(envs):
                if env_getter(env) == variation:
                    result.add(env)
                    break

    find_and_add(PYTHON_VERSIONS, lambda env: env.python_version)
    find_and_add(DJANGO_VERSIONS, lambda env: env.django_version)
    find_and_add(SETTINGS, lambda env: env.settings)

    return result


def make_tox_ini(envs):
    contents = ['''
[testenv]
whitelist_externals =
    sh
''']

    for idx, env in enumerate(envs):
        contents.append(testenv_config(idx, env))

    return '\n'.join(contents)


def make_travis_yml(envs):
    contents = """
language: python
python:
  - "3.3"
env:
%(testenvs)s
install:
  - pip install tox
script: tox -e $TESTENV
"""
    testenvs = '\n'.join('  - TESTENV=%s' % testenv_name(env) for env in envs)

    return contents % {
        'testenvs': testenvs
    }


def main():
    all_envs = sorted(generate_all_envs())
    unique_envs = sorted(generate_unique_envs(all_envs))

    with open('tox.ini', 'w+') as tox_ini_file:
        tox_ini_file.write(make_tox_ini(all_envs))

    with open('.travis.yml', 'w+') as travis_yml_file:
        travis_yml_file.write(make_travis_yml(unique_envs))

    print('Run unique envs locally with ')
    print()
    print('tox -e ' + ','.join(testenv_name(e) for e in unique_envs))
    print()
    print('detox -e ' + ','.join(testenv_name(e) for e in unique_envs))


if __name__ == '__main__':
    main()
