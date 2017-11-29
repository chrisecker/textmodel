# -*- coding: latin-1 -*-


from setuptools import setup

# NOTE: if there is a problem with symlinks, update setuptools:
# http://stackoverflow.com/questions/27459888/how-to-make-setuptools-follow-symlinks

with open('README') as file:
    long_description = file.read()

setup(name='rnb',
      version='0.2.3',
      description = 'An experimental notebook application for the r programming language.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/rnb/',
      license='BSD',
      packages=['rnb/pynotebook', 'rnb/pynotebook/textmodel', 'rnb/pynotebook/wxtextview'],
      scripts=['rnb/rnb'],
      platforms = ['any'],
      install_requires=[
          'rpy2', 'pygments'
      ],
     )

