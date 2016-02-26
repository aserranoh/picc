#!/usr/bin/env python

from distutils.core import setup

setup(name='picc',
      version='0.0.1',
      description='A linker for PIC relocatable objects in COFF format',
      author='Antonio Serrano Hernandez',
      author_email='toni.serranoh@gmail.com',
      url='https://github.com/aserranoh/picc',
      license='GPLv3',
      requires=['intelhex'],
      packages=['picc'],
      package_dir={'': 'lib'},
      scripts=['picc', 'picc-objdump'],
      data_files=['data/processors.xml'],
     )

