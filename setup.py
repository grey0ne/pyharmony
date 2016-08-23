#!/usr/bin/env python

import setuptools

setuptools.setup(
  name='pyharmony',
  version='0.1',
  license='BSD',
  description='Logitech Hub API',
  author='Dan Sully',
  author_email='daniel-python@electricrain.com',
  url='https://github.com/dsully/pyharmony',
  platforms='any',

  packages=['pyharmony'],
  entry_points={
      'console_scripts': [
          'harmony=pyharmony.scripts:cli'
      ],
  },
  zip_safe=True,
  verbose=False,
)
