# -*- coding: latin-1 -*-

#!/usr/bin/env python

from distutils.core import setup

with open('README') as file:
    long_description = file.read()

setup(name='textmodel',
      version='0.3.3',
      description = \
          'A data type for storing and manipulating styled text data.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/textmodel/',
      license='See file LICENSE',
      packages=['textmodel'],
      platforms = ['any'],
     )

