# -*- coding: latin-1 -*-


from setuptools import setup


with open('README') as file:
    long_description = file.read()

setup(name='pnb',
      version='0.2.5.3',
      description = 'A beautiful and lightweight notebook interface for the ' \
                    'python interpreter.',
      long_description = long_description,
      author='C. Ecker',
      author_email='textmodelview@gmail.com',
      url='https://github.com/chrisecker/textmodel/tree/master/pynotebook',
      license='BSD',
      scripts=['bin/pnb'],
      install_requires = ['pynotebook >= 0.2.5.3'],
      platforms = "Linux, Mac OS X, Windows",
      keywords = ['Interactive', 'Interpreter', 'Notebook', 'Shell',
                  'WXPython'],
      classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
      ],      
     )

