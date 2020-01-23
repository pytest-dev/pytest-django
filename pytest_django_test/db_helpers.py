import os
import subprocess
import sqlite3

import pytest

from django.conf import settings
from django.utils.encoding import force_str


# Construct names for the "inner" database used in runpytest tests
_settings = settings.DATABASES["default"]

DB_NAME = _settings["NAME"]
TEST_DB_NAME = _settings["TEST"]["NAME"]

if _settings["ENGINE"] == "django.db.backends.sqlite3" and TEST_DB_NAME is None:
    TEST_DB_NAME = ":memory:"
else:
    DB_NAME += "_inner"

    if TEST_DB_NAME is None:
        # No explicit test db name was given, construct a default one
        TEST_DB_NAME = "test_{}_inner".format(DB_NAME)
    else:
        # An explicit test db name was given, is that as the base name
        TEST_DB_NAME = "{}_inner".format(TEST_DB_NAME)


def get_db_engine():
    return _settings["ENGINE"].split(".")[-1]


class CmdResult(object):
    def __init__(self, status_code, std_out, std_err):
        self.status_code = status_code
        self.std_out = std_out
        self.std_err = std_err


def run_cmd(*args):
    r = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutdata, stderrdata = r.communicate()
    ret = r.wait()
    return CmdResult(ret, stdoutdata, stderrdata)


def run_mysql(*args):
    user = _settings.get("USER", None)
    if user:  # pragma: no branch
        args = ("-u", user) + tuple(args)
    args = ("mysql",) + tuple(args)
    return run_cmd(*args)


def skip_if_sqlite_in_memory():
    if (
        _settings["ENGINE"] == "django.db.backends.sqlite3"
        and _settings["TEST"]["NAME"] is None
    ):
        pytest.skip("Do not test db reuse since database does not support it")


def _get_db_name(db_suffix=None):
    name = TEST_DB_NAME
    if db_suffix:
        name = "%s_%s" % (name, db_suffix)
    return name


def drop_database(db_suffix=None):
    name = _get_db_name(db_suffix)
    db_engine = get_db_engine()

    if db_engine == "postgresql_psycopg2":
        r = run_cmd("psql", "postgres", "-c", "DROP DATABASE %s" % name)
        assert "DROP DATABASE" in force_str(
            r.std_out
        ) or "does not exist" in force_str(r.std_err)
        return

    if db_engine == "mysql":
        r = run_mysql("-e", "DROP DATABASE %s" % name)
        assert "database doesn't exist" in force_str(r.std_err) or r.status_code == 0
        return

    assert db_engine == "sqlite3", "%s cannot be tested properly!" % db_engine
    assert name != ":memory:", "sqlite in-memory database cannot be dropped!"
    if os.path.exists(name):  # pragma: no branch
        os.unlink(name)


def db_exists(db_suffix=None):
    name = _get_db_name(db_suffix)
    db_engine = get_db_engine()

    if db_engine == "postgresql_psycopg2":
        r = run_cmd("psql", name, "-c", "SELECT 1")
        return r.status_code == 0

    if db_engine == "mysql":
        r = run_mysql(name, "-e", "SELECT 1")
        return r.status_code == 0

    assert db_engine == "sqlite3", "%s cannot be tested properly!" % db_engine
    assert TEST_DB_NAME != ":memory:", (
        "sqlite in-memory database cannot be checked for existence!")
    return os.path.exists(name)


def mark_database():
    db_engine = get_db_engine()

    if db_engine == "postgresql_psycopg2":
        r = run_cmd("psql", TEST_DB_NAME, "-c", "CREATE TABLE mark_table();")
        assert r.status_code == 0
        return

    if db_engine == "mysql":
        r = run_mysql(TEST_DB_NAME, "-e", "CREATE TABLE mark_table(kaka int);")
        assert r.status_code == 0
        return

    assert db_engine == "sqlite3", "%s cannot be tested properly!" % db_engine
    assert TEST_DB_NAME != ":memory:", (
        "sqlite in-memory database cannot be marked!")

    conn = sqlite3.connect(TEST_DB_NAME)
    try:
        with conn:
            conn.execute("CREATE TABLE mark_table(kaka int);")
    finally:  # Close the DB even if an error is raised
        conn.close()


def mark_exists():
    db_engine = get_db_engine()

    if db_engine == "postgresql_psycopg2":
        r = run_cmd("psql", TEST_DB_NAME, "-c", "SELECT 1 FROM mark_table")

        # When something pops out on std_out, we are good
        return bool(r.std_out)

    if db_engine == "mysql":
        r = run_mysql(TEST_DB_NAME, "-e", "SELECT 1 FROM mark_table")

        return r.status_code == 0

    assert db_engine == "sqlite3", "%s cannot be tested properly!" % db_engine
    assert TEST_DB_NAME != ":memory:", (
        "sqlite in-memory database cannot be checked for mark!")

    conn = sqlite3.connect(TEST_DB_NAME)
    try:
        with conn:
            conn.execute("SELECT 1 FROM mark_table")
            return True
    except sqlite3.OperationalError:
        return False
    finally:  # Close the DB even if an error is raised
        conn.close()
