.PHONY: docs test clean isort

VENV:=build/venv

export DJANGO_SETTINGS_MODULE?=pytest_django_test.settings_sqlite_file

test: $(VENV)/bin/pytest
	$(VENV)/bin/pytest

$(VENV)/bin/python $(VENV)/bin/pip:
	virtualenv $(VENV)

$(VENV)/bin/pytest: $(VENV)/bin/python requirements.txt
	$(VENV)/bin/pip install -Ur requirements.txt
	touch $@

docs:
	tox -e docs

# See setup.cfg for configuration.
isort:
	isort pytest_django pytest_django_test tests

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
