#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pytest-django',
    version='1.1',
    description='A Django plugin for py.test.',
    author='Andreas Pelme',
    author_email='andreas@pelme.se',
    maintainer="Andreas Pelme",
    maintainer_email="andreas@pelme.se",
    url='http://pytest-django.readthedocs.org/',
    packages=['pytest_django'],
    long_description=read('README.rst'),
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing'],
    # the following makes a plugin available to py.test
    entry_points={'pytest11': ['django = pytest_django']})
