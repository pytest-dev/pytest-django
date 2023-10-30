.PHONY: docs test clean isort

test:
	tox -e py311-dj42-sqlite_file

docs:
	tox -e docs

# See setup.cfg for configuration.
isort:
	isort pytest_django pytest_django_test tests

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
