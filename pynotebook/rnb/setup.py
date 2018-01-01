# -*- coding: latin-1 -*-


from setuptools import setup

with open('README') as file:
    long_description = file.read()

setup(name='rnb',
      version='0.2.4rc1',
      description = 'An experimental notebook application for the r programming language.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://pypi.python.org/pypi/rnb/',
      license='BSD',
      scripts=['bin/rnb'],
      install_requires=[
          'rpy2', 'pygments', 'pynotebook > 0.2.3'
      ],
      platforms = "Linux, Mac OS X, Windows",
      keywords = ['Interactive', 'Interpreter', 'Notebook', 'Shell', 'WXPython'],
      classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
      ],
)

