#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-django',
    use_scm_version=True,
    description='A Django plugin for pytest.',
    author='Andreas Pelme',
    author_email='andreas@pelme.se',
    maintainer="Andreas Pelme",
    maintainer_email="andreas@pelme.se",
    url='https://pytest-django.readthedocs.io/',
    license='BSD-3-Clause',
    packages=['pytest_django'],
    long_description=read('README.rst'),
    setup_requires=['setuptools_scm==1.11.1'],
    install_requires=['pytest>=2.9'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 ],
    # the following makes a plugin available to pytest
    entry_points={'pytest11': ['django = pytest_django.plugin']})
