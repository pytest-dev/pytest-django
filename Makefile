.PHONY: docs test clean fix

test:
	tox -e py311-dj42-sqlite_file

docs:
	tox -e docs

fix:
	ruff check --fix pytest_django pytest_django_test tests

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
