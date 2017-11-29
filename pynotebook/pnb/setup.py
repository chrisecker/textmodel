# -*- coding: latin-1 -*-


from setuptools import setup

# NOTE: if there is a problem with symlinks, update setuptools:
# http://stackoverflow.com/questions/27459888/how-to-make-setuptools-follow-symlinks

with open('README') as file:
    long_description = file.read()

setup(name='pnb',
      version='0.2.3rc1',
      description = 'A beautiful and lighweight notebook for the python interpreter.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://github.com/chrisecker/textmodel/tree/master/pynotebook',
      license='BSD',
      packages=['pnb/pynotebook', 'pnb/pynotebook/textmodel', 'pnb/pynotebook/wxtextview'],
      scripts=['pnb/pnb'],
      platforms = ['any'],
     )

