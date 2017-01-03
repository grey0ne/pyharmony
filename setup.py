#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

here = lambda *a: os.path.join(os.path.dirname(__file__), *a)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open(here('README.md')).read()
requirements = [x.strip() for x in open(here('requirements.txt')).readlines()]

setup(
    name='pyharmony',
    version='1.0.12',
    description='Python library for programmatically using a Logitech Harmony Link or Ultimate Hub.',
    long_description=readme,
    author='Ian Day',
    author_email='iandday@gmail.com',
    url='https://github.com/iandday/pyharmony',
    download_url = 'https://github.com/iandday/pyharmony/tarball/1.0.12',
    packages=['pyharmony'],
    package_dir={'pyharmony': 'pyharmony'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='pyharmony',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Home Automation',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    entry_points={
        'console_scripts': [
            'harmony = pyharmony.__main__:main'
        ]
    },
)
