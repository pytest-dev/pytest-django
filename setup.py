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
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    setup_requires=['setuptools_scm>=1.11.1'],
    install_requires=[
        'pytest>=3.6',
        'pathlib2;python_version<"3.4"',
    ],
    extras_require={
        'docs': [
            'sphinx',
            'sphinx_rtd_theme',
        ],
        'testing': [
            'Django',
            'django-configurations>=2.0',
            'six',
        ],
    },
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Framework :: Django',
                 'Framework :: Django :: 1.8',
                 'Framework :: Django :: 1.9',
                 'Framework :: Django :: 1.10',
                 'Framework :: Django :: 1.11',
                 'Framework :: Django :: 2.0',
                 'Framework :: Django :: 2.1',
                 'Framework :: Django :: 2.2',
                 'Framework :: Django :: 3.0',
                 'Framework :: Django :: 3.1',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Software Development :: Testing',
                 ],
    project_urls={
        'Source': 'https://github.com/pytest-dev/pytest-django',
        'Changelog': 'https://pytest-django.readthedocs.io/en/latest/changelog.html',
    },
    # the following makes a plugin available to pytest
    entry_points={'pytest11': ['django = pytest_django.plugin']})
