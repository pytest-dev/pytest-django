.PHONY: docs test clean

testenv: bin/py.test


bin/python:
	virtualenv .

bin/py.test: bin/python
	bin/pip install -Ur requirements.txt

test: bin/py.test
	bin/pip install -Ur requirements.txt
	bin/py.test

bin/sphinx-build:
	bin/pip install sphinx

docs: bin/sphinx-build
	SPHINXBUILD=../bin/sphinx-build $(MAKE) -C docs html

clean:
	rm -rf bin include/ lib/ man/ pytest_django.egg-info/ build/
