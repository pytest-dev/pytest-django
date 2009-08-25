#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
 
setup(
    name='pytest_django',
    version='0.1',
    description='A Django plugin for py.test.',
    author='Ben Firshman',
    author_email='ben@firshman.co.uk',
    url='http://github.com/bfirsh/pytest_django/',
    packages=[
        'pytest_django',
    ],
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing'],
)
