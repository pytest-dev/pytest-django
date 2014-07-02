.PHONY: docs test clean

export DJANGO_SETTINGS_MODULE?=tests.settings_sqlite

testenv: bin/py.test


bin/python bin/pip:
	virtualenv .

bin/py.test: bin/python requirements.txt
	bin/pip install -Ur requirements.txt
	touch $@

test: bin/py.test
	bin/pip install -e .
	bin/py.test

bin/sphinx-build: bin/pip
	bin/pip install sphinx

docs: bin/sphinx-build
	SPHINXBUILD=../bin/sphinx-build $(MAKE) -C docs html

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
