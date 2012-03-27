#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pytest-django-pp',
    version='1.0.0',
    description='A Django plugin for py.test.',
    author='Ben Firshman',
    author_email='ben@firshman.co.uk',
    maintainer="pediapress",
    maintainer_email="development@pediapress.com",
    url='https://github.com/pediapress/pytest_django',
    packages=['pytest_django'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing'],
    # the following makes a plugin available to py.test
    entry_points=dict(pytest11=['django = pytest_django']))
