# -*- coding: latin-1 -*-


from setuptools import setup

# NOTE: if there is a problem with symlinks, update setuptools:
# http://stackoverflow.com/questions/27459888/how-to-make-setuptools-follow-symlinks

with open('README') as file:
    long_description = file.read()

setup(name='pynb',
      version='0.2.2',
      description = 'A beautiful and lighweight notebook for the python interpreter',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/pynotebook/',
      license='BSD',
      packages=['pynb/pynotebook', 'pynb/pynotebook/textmodel', 'pynb/pynotebook/wxtextview'],
      scripts=['pynb/pynb'],
      platforms = ['any'],
     )

