from unittest.mock import Mock, call

import pytest

from pytest_django.runner import PytestTestRunner


@pytest.mark.parametrize(
    *(
        "kwargs, expected",
        [
            ({}, call(["tests"])),
            ({"verbosity": 0}, call(["--quiet", "tests"])),
            ({"verbosity": 1}, call(["tests"])),
            ({"verbosity": 2}, call(["--verbose", "tests"])),
            ({"verbosity": 3}, call(["-vv", "tests"])),
            ({"verbosity": 4}, call(["tests"])),
            ({"failfast": True}, call(["--exitfirst", "tests"])),
            ({"keepdb": True}, call(["--reuse-db", "tests"])),
        ],
    )
)
def test_runner_run_tests(monkeypatch, kwargs, expected):
    pytest_mock = Mock()
    monkeypatch.setattr("pytest.main", pytest_mock)
    runner = PytestTestRunner(**kwargs)
    runner.run_tests("tests")
    assert pytest_mock.call_args == expected
