# -*- coding: latin-1 -*-

#!/usr/bin/env python

from setuptools import setup

with open('README') as file:
    long_description = file.read()

setup(name='wxtextview',
      version='0.3.4',
      description = \
          'A styled text widget for wxpython.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/wxtextview/',
      license='BSD',
      packages=['wxtextview'],
      platforms = ['any'],
      install_requires = ['textmodel'],
     )

