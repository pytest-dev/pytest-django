#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pytest-django',
    version='1.0.0',
    description='A Django plugin for py.test.',
    author='Andreas Pelme',
    author_email='andreas@pelme.se',
    maintainer="Andreas Pelme",
    maintainer_email="andreas@pelme.se",
    url='https://github.com/pelme/pytest_django',
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
