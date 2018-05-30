.PHONY: docs test clean isort

VENV:=build/venv

export DJANGO_SETTINGS_MODULE?=pytest_django_test.settings_sqlite_file

testenv: $(VENV)/bin/pytest

test: $(VENV)/bin/pytest
	$(VENV)/bin/pip install -e .
	$(VENV)/bin/py.test

$(VENV)/bin/python $(VENV)/bin/pip:
	virtualenv $(VENV)

$(VENV)/bin/pytest: $(VENV)/bin/python requirements.txt
	$(VENV)/bin/pip install -Ur requirements.txt
	touch $@

docs:
	tox -e docs

# See setup.cfg for configuration.
isort:
	find pytest_django tests -name '*.py' -exec isort {} +

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
