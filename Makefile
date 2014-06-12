.PHONY: docs test clean

testenv: bin/py.test

export DJANGO_SETTINGS_MODULE?=tests.settings_sqlite

bin/python:
	virtualenv .

bin/py.test: bin/python
	bin/pip install -Ur requirements.txt

test: bin/py.test
	bin/pip install -Ur requirements.txt
	bin/py.test tests

bin/sphinx-build:
	bin/pip install sphinx

docs: bin/sphinx-build
	SPHINXBUILD=../bin/sphinx-build $(MAKE) -C docs html

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
