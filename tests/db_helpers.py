import envoy


DB_NAME = 'pytest_django_db_test'
TEST_DB_NAME = 'test_' + DB_NAME


def get_db_engine():
    from django.conf import settings
    return settings.DATABASES['default']['ENGINE'].split('.')[-1]


def create_empty_production_database():
    drop_database(name=DB_NAME)

    if get_db_engine() == 'postgresql_psycopg2':
        r = envoy.run('echo CREATE DATABASE %s | psql postgres' % DB_NAME)
        assert 'CREATE DATABASE' in r.std_out or 'already exists' in r.std_err
        return

    if get_db_engine() == 'mysql':
        r = envoy.run('echo CREATE DATABASE %s | mysql' % DB_NAME)
        assert r.status_code == 0 or 'database exists' in r.std_out
        return

    raise AssertionError('%s cannot be tested properly' % get_db_engine())


def drop_database(name=TEST_DB_NAME):
    if get_db_engine() == 'postgresql_psycopg2':
        r = envoy.run('echo DROP DATABASE %s | psql postgres' % name)
        assert r.status_code == 0
        assert 'DROP DATABASE' in r.std_out or 'does not exist' in r.std_err
        return

    if get_db_engine() == 'mysql':
        r = envoy.run('echo DROP DATABASE %s | mysql -u root' % name)
        assert ('database doesn\'t exist' in r.std_err
                or r.status_code == 0)
        return

    raise AssertionError('%s cannot be tested properly!' % get_db_engine())


def db_exists():
    if get_db_engine() == 'postgresql_psycopg2':
        r = envoy.run('echo SELECT 1 | psql %s' % TEST_DB_NAME)
        return r.status_code == 0

    if get_db_engine() == 'mysql':
        r = envoy.run('echo SELECT 1 | mysql %s' % TEST_DB_NAME)
        return r.status_code == 0

    raise AssertionError('%s cannot be tested properly!' % get_db_engine())


def mark_database():
    if get_db_engine() == 'postgresql_psycopg2':
        r = envoy.run('echo CREATE TABLE mark_table(); | psql %s' % TEST_DB_NAME)
        assert r.status_code == 0
        return

    if get_db_engine() == 'mysql':
        r = envoy.run('echo CREATE TABLE mark_table(kaka int); | mysql %s' % TEST_DB_NAME)
        assert r.status_code == 0
        return

    raise AssertionError('%s cannot be tested properly!' % get_db_engine())


def mark_exists():
    if get_db_engine() == 'postgresql_psycopg2':
        f = envoy.run('echo SELECT 1 FROM mark_table | psql %s' % TEST_DB_NAME)
        assert f.status_code == 0

        # When something pops out on std_out, we are good
        return bool(f.std_out)

    if get_db_engine() == 'mysql':
        f = envoy.run('echo SELECT 1 FROM mark_table | mysql %s' % TEST_DB_NAME)
        return f.status_code == 0

    raise AssertionError('%s cannot be tested properly!' % get_db_engine())

