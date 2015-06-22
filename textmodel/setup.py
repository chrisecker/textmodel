# -*- coding: latin-1 -*-

#!/usr/bin/env python

from setuptools import setup

with open('README') as file:
    long_description = file.read()

setup(name='textmodel',
      version='0.3.4',
      description = \
          'A data type for storing and manipulating rich text data. ' \
          'It aims to be fast and efficient and it is suited even for ' \
          'very long texts.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/textmodel/',
      license='BSD',
      packages=['textmodel'],
      platforms = ['any'],
     )

